library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity z80_minimal_top is
	port(
		clk             : in  std_logic;
		reset_n         : in  std_logic;
		halted          : out std_logic;
		ram8000_value   : out std_logic_vector(7 downto 0);
		refresh_count   : out std_logic_vector(7 downto 0);
		video_read_count: out std_logic_vector(7 downto 0);
		cpu_wait_count  : out std_logic_vector(7 downto 0);
		io_write_seen   : out std_logic;
		io_write_port   : out std_logic_vector(7 downto 0);
		io_write_value  : out std_logic_vector(7 downto 0);
		key_read_seen   : out std_logic;
		vga_frame_seen  : out std_logic;
		hsync_n         : out std_logic;
		vsync_n         : out std_logic
	);
end z80_minimal_top;

architecture rtl of z80_minimal_top is
	component T80se is
		generic(
			Mode    : integer := 0;
			T2Write : integer := 0;
			IOWait  : integer := 1
		);
		port(
			RESET_n : in  std_logic;
			CLK_n   : in  std_logic;
			CLKEN   : in  std_logic;
			WAIT_n  : in  std_logic;
			INT_n   : in  std_logic;
			NMI_n   : in  std_logic;
			BUSRQ_n : in  std_logic;
			M1_n    : out std_logic;
			MREQ_n  : out std_logic;
			IORQ_n  : out std_logic;
			RD_n    : out std_logic;
			WR_n    : out std_logic;
			RFSH_n  : out std_logic;
			HALT_n  : out std_logic;
			BUSAK_n : out std_logic;
			A       : out std_logic_vector(15 downto 0);
			DI      : in  std_logic_vector(7 downto 0);
			DO      : out std_logic_vector(7 downto 0)
		);
	end component;

	type dram_bit_t is array (0 to 65535) of std_logic;
	type dram_bank_t is array (0 to 7) of dram_bit_t;
	type dram_client_t is (CLIENT_CPU, CLIENT_VIDEO);
	type dram_state_t is (DRAM_IDLE, DRAM_ROW, DRAM_RAS, DRAM_COL, DRAM_CAS, DRAM_DONE,
	                      DRAM_REF_ROW, DRAM_REF_RAS, DRAM_REF_DONE);

	signal a       : std_logic_vector(15 downto 0);
	signal di      : std_logic_vector(7 downto 0);
	signal do_cpu  : std_logic_vector(7 downto 0);
	signal mreq_n  : std_logic;
	signal iorq_n  : std_logic;
	signal rd_n    : std_logic;
	signal wr_n    : std_logic;
	signal halt_n  : std_logic;
	signal wait_n_s : std_logic := '1';
	signal m1_n    : std_logic;
	signal rfsh_n  : std_logic;
	signal busak_n : std_logic;

	signal dram : dram_bank_t := (others => (others => '0'));
	signal io_seen_r : std_logic := '0';
	signal io_port_r : std_logic_vector(7 downto 0) := (others => '0');
	signal io_data_r : std_logic_vector(7 downto 0) := (others => '0');
	signal key_seen_r : std_logic := '0';
	signal refresh_ctr : unsigned(7 downto 0) := (others => '0');
	signal refresh_div : unsigned(7 downto 0) := (others => '0');
	signal refresh_req : std_logic := '0';
	signal dram_state : dram_state_t := DRAM_IDLE;
	signal dram_client : dram_client_t := CLIENT_CPU;
	signal dram_addr : std_logic_vector(15 downto 0) := (others => '0');
	signal dram_cpu_write : std_logic := '0';
	signal dram_write_data : std_logic_vector(7 downto 0) := (others => '0');
	signal dram_read_latch : std_logic_vector(7 downto 0) := (others => '0');
	signal video_read_latch : std_logic_vector(7 downto 0) := (others => '0');
	signal video_addr : unsigned(15 downto 0) := x"8000";
	signal video_req : std_logic := '0';
	signal video_ctr : unsigned(7 downto 0) := (others => '0');
	signal video_div : unsigned(5 downto 0) := (others => '0');
	signal cpu_wait_ctr : unsigned(7 downto 0) := (others => '0');
	signal dram_ma : std_logic_vector(7 downto 0) := (others => '0');
	signal dram_ras_n : std_logic := '1';
	signal dram_cas_n : std_logic := '1';
	signal dram_we_n : std_logic := '1';
	signal vga_x : unsigned(9 downto 0) := (others => '0');
	signal vga_y : unsigned(9 downto 0) := (others => '0');
	signal vga_frame_r : std_logic := '0';
	signal hsync_r : std_logic := '1';
	signal vsync_r : std_logic := '1';

	function dram_read(bank : dram_bank_t; addr : std_logic_vector(15 downto 0)) return std_logic_vector is
		variable q : std_logic_vector(7 downto 0);
		variable ix : natural := to_integer(unsigned(addr));
	begin
		for i in 0 to 7 loop
			q(i) := bank(i)(ix);
		end loop;
		return q;
	end function;

	function rom_byte(addr : std_logic_vector(15 downto 0)) return std_logic_vector is
		variable ix : natural := to_integer(unsigned(addr(3 downto 0)));
	begin
		case ix is
			when 0  => return x"3E"; -- LD A,0x42
			when 1  => return x"42";
			when 2  => return x"32"; -- LD (0x8000),A
			when 3  => return x"00";
			when 4  => return x"80";
			when 5  => return x"3A"; -- LD A,(0x8000)
			when 6  => return x"00";
			when 7  => return x"80";
			when 8  => return x"D3"; -- OUT (0x10),A
			when 9  => return x"10";
			when 10 => return x"DB"; -- IN A,(0x20)
			when 11 => return x"20";
			when 12 => return x"76"; -- HALT
			when others => return x"00";
		end case;
	end function;
begin
	u_cpu : T80se
		generic map(
			Mode    => 0,
			T2Write => 0,
			IOWait  => 1
		)
		port map(
			RESET_n => reset_n,
			CLK_n   => clk,
			CLKEN   => '1',
			WAIT_n  => wait_n_s,
			INT_n   => '1',
			NMI_n   => '1',
			BUSRQ_n => '1',
			M1_n    => m1_n,
			MREQ_n  => mreq_n,
			IORQ_n  => iorq_n,
			RD_n    => rd_n,
			WR_n    => wr_n,
			RFSH_n  => rfsh_n,
			HALT_n  => halt_n,
			BUSAK_n => busak_n,
			A       => a,
			DI      => di,
			DO      => do_cpu
		);

	wait_n_s <= '0' when mreq_n = '0' and rd_n = '0' and a(15) = '1' and dram_state /= DRAM_DONE else '1';

	di <= x"A5" when iorq_n = '0' and rd_n = '0' and a(7 downto 0) = x"20" else
	      rom_byte(a) when mreq_n = '0' and rd_n = '0' and a(15) = '0' else
	      dram_read_latch when mreq_n = '0' and rd_n = '0' and a(15) = '1' else
	      x"FF";

	process(clk)
	begin
		if rising_edge(clk) then
			if reset_n = '0' then
				dram <= (others => (others => '0'));
				io_seen_r <= '0';
				io_port_r <= (others => '0');
				io_data_r <= (others => '0');
				key_seen_r <= '0';
				refresh_ctr <= (others => '0');
				refresh_div <= (others => '0');
				refresh_req <= '0';
				dram_state <= DRAM_IDLE;
				dram_client <= CLIENT_CPU;
				dram_addr <= (others => '0');
				dram_cpu_write <= '0';
				dram_write_data <= (others => '0');
				dram_read_latch <= (others => '0');
				video_read_latch <= (others => '0');
				video_addr <= x"8000";
				video_req <= '0';
				video_ctr <= (others => '0');
				video_div <= (others => '0');
				cpu_wait_ctr <= (others => '0');
				dram_ma <= (others => '0');
				dram_ras_n <= '1';
				dram_cas_n <= '1';
				dram_we_n <= '1';
				vga_x <= (others => '0');
				vga_y <= (others => '0');
				vga_frame_r <= '0';
				hsync_r <= '1';
				vsync_r <= '1';
			else
				dram_ras_n <= '1';
				dram_cas_n <= '1';
				dram_we_n <= '1';
				if iorq_n = '0' and wr_n = '0' then
					io_seen_r <= '1';
					io_port_r <= a(7 downto 0);
					io_data_r <= do_cpu;
				end if;
				if iorq_n = '0' and rd_n = '0' and a(7 downto 0) = x"20" then
					key_seen_r <= '1';
				end if;

				if wait_n_s = '0' then
					cpu_wait_ctr <= cpu_wait_ctr + 1;
				end if;

				refresh_div <= refresh_div + 1;
				if refresh_div = 255 then
					refresh_req <= '1';
				end if;

				video_div <= video_div + 1;
				if video_div = 63 then
					video_req <= '1';
				end if;

				case dram_state is
					when DRAM_IDLE =>
						if mreq_n = '0' and a(15) = '1' and (rd_n = '0' or wr_n = '0') then
							dram_client <= CLIENT_CPU;
							dram_addr <= a;
							dram_cpu_write <= not wr_n;
							dram_write_data <= do_cpu;
							dram_ma <= a(15 downto 8);
							dram_state <= DRAM_ROW;
						elsif refresh_req = '1' then
							dram_ma <= std_logic_vector(refresh_ctr);
							dram_state <= DRAM_REF_ROW;
						elsif video_req = '1' then
							dram_client <= CLIENT_VIDEO;
							dram_addr <= std_logic_vector(video_addr);
							dram_cpu_write <= '0';
							dram_ma <= std_logic_vector(video_addr(15 downto 8));
							dram_state <= DRAM_ROW;
						end if;
					when DRAM_ROW =>
						dram_ras_n <= '0';
						dram_state <= DRAM_RAS;
					when DRAM_RAS =>
						dram_ras_n <= '0';
						dram_ma <= dram_addr(7 downto 0);
						dram_we_n <= not dram_cpu_write;
						dram_state <= DRAM_COL;
					when DRAM_COL =>
						dram_ras_n <= '0';
						dram_cas_n <= '0';
						dram_we_n <= not dram_cpu_write;
						if dram_cpu_write = '1' then
							for i in 0 to 7 loop
								dram(i)(to_integer(unsigned(dram_addr))) <= dram_write_data(i);
							end loop;
							dram_read_latch <= dram_write_data;
						else
							if dram_client = CLIENT_CPU then
								dram_read_latch <= dram_read(dram, dram_addr);
							else
								video_read_latch <= dram_read(dram, dram_addr);
							end if;
						end if;
						dram_state <= DRAM_CAS;
					when DRAM_CAS =>
						dram_ras_n <= '0';
						dram_cas_n <= '0';
						dram_we_n <= not dram_cpu_write;
						dram_state <= DRAM_DONE;
					when DRAM_DONE =>
						if dram_client = CLIENT_VIDEO then
							video_ctr <= video_ctr + 1;
							video_addr <= video_addr + 1;
							video_req <= '0';
						end if;
						dram_state <= DRAM_IDLE;
					when DRAM_REF_ROW =>
						dram_ras_n <= '0';
						refresh_ctr <= refresh_ctr + 1;
						refresh_req <= '0';
						dram_state <= DRAM_REF_RAS;
					when DRAM_REF_RAS =>
						dram_ras_n <= '0';
						dram_state <= DRAM_REF_DONE;
					when DRAM_REF_DONE =>
						dram_state <= DRAM_IDLE;
				end case;

				if vga_x = 799 then
					vga_x <= (others => '0');
					if vga_y = 524 then
						vga_y <= (others => '0');
						vga_frame_r <= '1';
					else
						vga_y <= vga_y + 1;
					end if;
				else
					vga_x <= vga_x + 1;
				end if;
				hsync_r <= '0' when vga_x >= 656 and vga_x < 752 else '1';
				vsync_r <= '0' when vga_y >= 490 and vga_y < 492 else '1';
			end if;
		end if;
	end process;

	halted <= not halt_n;
	ram8000_value <= dram_read(dram, x"8000");
	refresh_count <= std_logic_vector(refresh_ctr);
	video_read_count <= std_logic_vector(video_ctr);
	cpu_wait_count <= std_logic_vector(cpu_wait_ctr);
	io_write_seen <= io_seen_r;
	io_write_port <= io_port_r;
	io_write_value <= io_data_r;
	key_read_seen <= key_seen_r;
	vga_frame_seen <= vga_frame_r;
	hsync_n <= hsync_r;
	vsync_n <= vsync_r;
end rtl;
