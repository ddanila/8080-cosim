library ieee;
use ieee.std_logic_1164.all;
use std.env.all;

entity z80_minimal_tb is
end z80_minimal_tb;

architecture sim of z80_minimal_tb is
	signal clk            : std_logic := '0';
	signal reset_n        : std_logic := '0';
	signal halted         : std_logic;
	signal ram8000_value  : std_logic_vector(7 downto 0);
	signal refresh_count  : std_logic_vector(7 downto 0);
	signal video_read_count : std_logic_vector(7 downto 0);
	signal cpu_wait_count : std_logic_vector(7 downto 0);
	signal io_write_seen  : std_logic;
	signal io_write_port  : std_logic_vector(7 downto 0);
	signal io_write_value : std_logic_vector(7 downto 0);
	signal key_read_seen  : std_logic;
	signal vga_frame_seen : std_logic;
	signal hsync_n        : std_logic;
	signal vsync_n        : std_logic;
begin
	clk <= not clk after 5 ns;

	uut : entity work.z80_minimal_top
		port map(
			clk            => clk,
			reset_n        => reset_n,
			halted         => halted,
			ram8000_value  => ram8000_value,
			refresh_count   => refresh_count,
			video_read_count => video_read_count,
			cpu_wait_count  => cpu_wait_count,
			io_write_seen  => io_write_seen,
			io_write_port  => io_write_port,
			io_write_value => io_write_value,
			key_read_seen  => key_read_seen,
			vga_frame_seen => vga_frame_seen,
			hsync_n        => hsync_n,
			vsync_n        => vsync_n
		);

	process
	begin
		wait for 50 ns;
		reset_n <= '1';

		for i in 0 to 500 loop
			wait until rising_edge(clk);
			if halted = '1' then
				assert ram8000_value = x"42"
					report "RAM[0x8000] did not receive 0x42"
					severity failure;
				assert io_write_seen = '1'
					report "IO write was not observed"
					severity failure;
				assert io_write_port = x"10"
					report "IO write used the wrong port"
					severity failure;
				assert io_write_value = x"42"
					report "IO write used the wrong value"
					severity failure;
				assert key_read_seen = '1'
					report "Keyboard/IO read was not observed"
					severity failure;
				wait for 5 ms;
				assert refresh_count /= x"00"
					report "Independent DRAM refresh counter did not tick"
					severity failure;
				assert video_read_count /= x"00"
					report "Video DRAM reads did not occur"
					severity failure;
				assert cpu_wait_count /= x"00"
					report "CPU was not wait-stated for DRAM reads"
					severity failure;
				assert vga_frame_seen = '1'
					report "VGA timing did not complete a frame"
					severity failure;
				report "[Z80-MIN] PASS: T80 ROM, DRAM arbitration, refresh, video reads, keyboard IO, VGA timing";
				stop;
			end if;
		end loop;

		assert false report "T80 smoke program did not halt in time" severity failure;
	end process;
end sim;
