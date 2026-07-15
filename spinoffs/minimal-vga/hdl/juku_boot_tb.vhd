-- Testbench: clock/reset the VJUGA Juku-boot top until it has drawn `vw_limit`
-- video writes, at which point the top dumps its framebuffer and calls finish.
-- A watchdog fails the run if that never happens.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity juku_boot_tb is
	generic(
		rom_file  : string  := "ekta37.hex";
		vw_limit  : natural := 6000;
		dump_file : string  := "vjuga_vram.bin";
		cpu_mode  : integer := 0   -- Z80 mode (see juku_boot_top); use patched ekta37_z80 ROM
	);
end entity;

architecture tb of juku_boot_tb is
	signal clk      : std_logic := '0';
	signal reset_n  : std_logic := '0';
	signal halted   : std_logic;
	signal vw_count : std_logic_vector(31 downto 0);
	signal cur_mode : std_logic_vector(1 downto 0);
	signal stop_clk : boolean := false;
begin
	dut : entity work.juku_boot_top
		generic map(rom_file => rom_file, vw_limit => vw_limit,
		            dump_file => dump_file, cpu_mode => cpu_mode)
		port map(clk => clk, reset_n => reset_n, halted => halted,
		         vw_count => vw_count, cur_mode => cur_mode);

	clk <= not clk after 10 ns when not stop_clk else '0';

	stimulus : process
	begin
		reset_n <= '0';
		wait for 100 ns;
		reset_n <= '1';
		-- Bounded watchdog: the top calls std.env.finish when vw_limit is reached.
		-- If it does not, fail here rather than hang.
		wait for 4000 ms;
		assert false
			report "juku_boot_tb: video-write target not reached (vw="
			       & integer'image(to_integer(unsigned(vw_count))) & ")"
			severity failure;
		stop_clk <= true;
		wait;
	end process;
end tb;
