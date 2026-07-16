-- VJUGA Juku-boot top: run the REAL Juku ekta37 ROM on the Z80 (T80) core with
-- the Juku memory map reused from the main recreation, and dump the framebuffer
-- so it can be compared byte-for-byte against the cosim oracle (cosim/vram.bin).
--
-- What is REUSED from the 8080-cosim recreation (the point of VJUGA):
--   * roms/ekta37.bin           -- the real boot ROM (loaded as ekta37.hex)
--   * the Juku memory map        -- modes 0..3 selected by 8255 Port C bits 0..1,
--                                  faithful to cosim/trace.c (MAME ussr/juku.cpp):
--       mode 0 (reset): ROM 0x0000..0x3FFF
--       mode 1:         ROM 0xD800..0xFFFF  (ROM offset 0x1800), rest RAM
--       mode 2:         expcart 0x4000..0xBFFF (empty->0xFF) + ROM 0xD800..0xFFFF
--       mode 3:         all RAM
--   * the video framebuffer      -- DRAM at 0xD800, 40 bytes/line x 241 lines
--   * cosim as the reference oracle (validation is done outside, in boot_check)
--
-- Deliberately minimal per the VJUGA charter (no bus outputs, no FDC): a flat
-- 64K RAM stands in for the bit-sliced РУ5 array + sequencer used by the smoke
-- top; the frame interrupt is OFF (the ekta37 banner draws without it, exactly
-- as cosim runs it with frame_cyc=0). IN ports return the 8255 output latch
-- (no key held), matching cosim with the keyboard disabled.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;
use std.env.all;

entity juku_boot_top is
	generic(
		rom_file  : string  := "ekta37.hex";  -- one 2-hex-digit byte per line
		vw_limit  : natural := 6000;           -- stop+dump after N video writes (match boot_check)
		dump_file : string  := "vjuga_vram.bin";
		-- T80 Mode: 0=Z80, 2=8080. VJUGA is a single-+5 V Z80 board (mode 0). The stock
		-- Juku firmware is 8080 code for the КР580ВМ80 and its bytes 0x08/0x10/0x20 are
		-- NOPs on the 8080 but real instructions (EX AF/DJNZ/JR) on a Z80, so it must be
		-- run either in 8080 mode (2) or, on a real Z80, with the 3-byte-patched
		-- ekta37_z80.bin ROM (see ../roms/README.md). Default: Z80.
		cpu_mode  : integer := 0
	);
	port(
		clk      : in  std_logic;
		reset_n  : in  std_logic;
		halted   : out std_logic;
		vw_count : out std_logic_vector(31 downto 0);
		cur_mode : out std_logic_vector(1 downto 0)
	);
end entity;

architecture rtl of juku_boot_top is
	component T80se is
		generic(Mode : integer := 0; T2Write : integer := 0; IOWait : integer := 1);
		port(
			RESET_n : in  std_logic; CLK_n : in std_logic; CLKEN : in std_logic;
			WAIT_n  : in  std_logic; INT_n : in std_logic; NMI_n : in std_logic;
			BUSRQ_n : in  std_logic;
			M1_n    : out std_logic; MREQ_n : out std_logic; IORQ_n : out std_logic;
			RD_n    : out std_logic; WR_n : out std_logic; RFSH_n : out std_logic;
			HALT_n  : out std_logic; BUSAK_n : out std_logic;
			A       : out std_logic_vector(15 downto 0);
			DI      : in  std_logic_vector(7 downto 0);
			DO      : out std_logic_vector(7 downto 0)
		);
	end component;

	subtype byte_value is natural range 0 to 255;
	type byte_arr is array (natural range <>) of byte_value;
	type byte_arr_ptr is access byte_arr;

	-- A protected variable keeps the behavioral 64 KiB RAM as storage rather
	-- than 524,288 individually scheduled std_logic signals. This is both closer
	-- to the intended memory abstraction and avoids multi-gigabyte elaboration
	-- overhead in GHDL's mcode backend.
	type ram_store_t is protected
		procedure put(addr : natural; data : std_logic_vector(7 downto 0));
		procedure load_hex(fn : string; n : natural);
		impure function get(addr : natural) return std_logic_vector;
	end protected;

	type ram_store_t is protected body
		variable mem : byte_arr_ptr := new byte_arr(0 to 65535);
		procedure put(addr : natural; data : std_logic_vector(7 downto 0)) is
		begin
			mem(addr) := to_integer(unsigned(data));
		end procedure;
		procedure load_hex(fn : string; n : natural) is
			file f : text;
			variable status : file_open_status;
			variable l : line;
			variable b : std_logic_vector(7 downto 0);
			variable i : natural := 0;
		begin
			file_open(status, f, fn, read_mode);
			assert status = open_ok report "juku_boot_top: cannot open ROM " & fn severity failure;
			while (not endfile(f)) and i < n loop
				readline(f, l);
				if l'length > 0 then
					hread(l, b);
					mem(i) := to_integer(unsigned(b));
					i := i + 1;
				end if;
			end loop;
			file_close(f);
			assert i = n report "juku_boot_top: short ROM read" severity failure;
		end procedure;
		impure function get(addr : natural) return std_logic_vector is
		begin
			return std_logic_vector(to_unsigned(mem(addr), 8));
		end function;
	end protected body;

	shared variable rom : ram_store_t;
	shared variable ram : ram_store_t;

	signal a      : std_logic_vector(15 downto 0);
	signal di     : std_logic_vector(7 downto 0);
	signal do_cpu : std_logic_vector(7 downto 0);
	signal mreq_n, iorq_n, rd_n, wr_n, m1_n, rfsh_n, halt_n, busak_n : std_logic;

	signal mode      : unsigned(1 downto 0) := "00";
	signal portc     : std_logic_vector(7 downto 0) := (others => '0');
	type   out_latch_t is array (0 to 255) of std_logic_vector(7 downto 0);
	signal out_last  : out_latch_t := (others => (others => '0'));
	signal vw        : unsigned(31 downto 0) := (others => '0');
	signal prev_wr_n, prev_iow_n : std_logic := '1';

	-- Combinational overlay read (rom/cart/ram) matching cosim rb()/overlay().
	impure function read_byte(addr : std_logic_vector(15 downto 0)) return std_logic_vector is
		variable ua  : unsigned(15 downto 0) := unsigned(addr);
		variable idx : natural;
	begin
		case to_integer(mode) is
			when 0 =>
				if ua <= 16#3FFF# then return rom.get(to_integer(ua)); end if;
			when 1 =>
				if ua >= 16#D800# then
					idx := 16#1800# + (to_integer(ua) - 16#D800#);
					return rom.get(idx);
				end if;
			when 2 =>
				if ua >= 16#4000# and ua <= 16#BFFF# then return x"FF"; end if;  -- empty expcart
				if ua >= 16#D800# then
					idx := 16#1800# + (to_integer(ua) - 16#D800#);
					return rom.get(idx);
				end if;
			when others => null;  -- mode 3: all RAM
		end case;
		return ram.get(to_integer(ua));
	end function;

	-- Is address served by a ROM/cart overlay in the current mode? (writes under it are dropped)
	impure function is_overlay(addr : std_logic_vector(15 downto 0)) return boolean is
		variable ua : unsigned(15 downto 0) := unsigned(addr);
	begin
		case to_integer(mode) is
			when 0 => return ua <= 16#3FFF#;
			when 1 => return ua >= 16#D800#;
			when 2 => return (ua >= 16#4000# and ua <= 16#BFFF#) or (ua >= 16#D800#);
			when others => return false;
		end case;
	end function;
begin
	rom_init : process
	begin
		rom.load_hex(rom_file, 16384);
		wait;
	end process;

	u_cpu : T80se
		generic map(Mode => cpu_mode, T2Write => 0, IOWait => 1)
		port map(
			RESET_n => reset_n, CLK_n => clk, CLKEN => '1',
			WAIT_n => '1', INT_n => '1', NMI_n => '1', BUSRQ_n => '1',
			M1_n => m1_n, MREQ_n => mreq_n, IORQ_n => iorq_n,
			RD_n => rd_n, WR_n => wr_n, RFSH_n => rfsh_n,
			HALT_n => halt_n, BUSAK_n => busak_n,
			A => a, DI => di, DO => do_cpu
		);

	-- Async CPU read bus. Deliberately react to bus/control changes rather than
	-- every element of the 64 KiB signal RAM: CPU writes and reads are separate
	-- cycles, so a later address/read transition always observes the new value.
	-- Including the whole RAM through process(all) makes GHDL elaborate an
	-- enormous simulation-only sensitivity list without improving this model.
	read_bus : process(a, mreq_n, iorq_n, rd_n, mode)
	begin
		if mreq_n = '0' and rd_n = '0' then
			di <= read_byte(a);
		elsif iorq_n = '0' and rd_n = '0' then
			di <= out_last(to_integer(unsigned(a(7 downto 0))));
		else
			di <= x"FF";
		end if;
	end process;

	process(clk)
		variable p    : integer;
		variable bitn : integer;
	begin
		if rising_edge(clk) then
			if reset_n = '0' then
				mode      <= "00";
				portc     <= (others => '0');
				vw        <= (others => '0');
				prev_wr_n <= '1';
				prev_iow_n<= '1';
			else
				-- Memory write (once per cycle, on the WR falling edge), dropped under an overlay.
				if mreq_n = '0' and wr_n = '0' and prev_wr_n = '1' then
					if not is_overlay(a) then
						ram.put(to_integer(unsigned(a)), do_cpu);
						if unsigned(a) >= 16#D800# then
							vw <= vw + 1;
						end if;
					end if;
				end if;
				prev_wr_n <= wr_n or mreq_n;

				-- IO write (once per cycle): latch, and decode the 8255 Port C bank control.
				if iorq_n = '0' and wr_n = '0' and prev_iow_n = '1' then
					p := to_integer(unsigned(a(7 downto 0)));
					out_last(p) <= do_cpu;
					if p = 16#06# then                    -- direct Port C write
						portc <= do_cpu;
						mode  <= unsigned(do_cpu(1 downto 0));
					elsif p = 16#07# then                  -- 8255 control port
						if do_cpu(7) = '1' then             -- mode-set command: outputs reset
							portc <= (others => '0');
							mode  <= "00";
						else                                 -- Port C bit set/reset
							bitn := to_integer(unsigned(do_cpu(3 downto 1)));
							if do_cpu(0) = '1' then
								portc(bitn) <= '1';
							else
								portc(bitn) <= '0';
							end if;
							if bitn = 0 then mode(0) <= do_cpu(0); end if;
							if bitn = 1 then mode(1) <= do_cpu(0); end if;
						end if;
					end if;
				end if;
				prev_iow_n <= wr_n or iorq_n;
			end if;
		end if;
	end process;

	-- When the target video-write count is reached, dump the 40x241 framebuffer at
	-- 0xD800 (byte order identical to cosim's vram.bin) and stop, so boot_check can
	-- compare the two files byte-for-byte.
	dump_proc : process(clk)
		type     charfile is file of character;
		file     fo       : charfile;
		variable st       : file_open_status;
		variable b        : std_logic_vector(7 downto 0);
	begin
		if rising_edge(clk) then
			if reset_n = '1' and vw_limit > 0 and vw = to_unsigned(vw_limit, vw'length) then
				file_open(st, fo, dump_file, write_mode);
				assert st = open_ok report "juku_boot_top: cannot open dump file" severity failure;
				for i in 0 to (40*241 - 1) loop
					b := ram.get(16#D800# + i);
					write(fo, character'val(to_integer(unsigned(b))));
				end loop;
				file_close(fo);
				report "juku_boot_top: framebuffer dumped after " & integer'image(vw_limit)
				       & " video writes (mode=" & integer'image(to_integer(mode)) & ")";
				finish;
			end if;
		end if;
	end process;

	halted   <= not halt_n;
	vw_count <= std_logic_vector(vw);
	cur_mode <= std_logic_vector(mode);
end rtl;
