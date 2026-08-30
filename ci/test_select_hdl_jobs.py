#!/usr/bin/env python3
"""Table-driven regression tests for the fail-open HDL lane selector."""

from __future__ import annotations

import unittest

from ci.select_hdl_jobs import load_manifest, select_jobs


class SelectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest()
        cls.all_jobs = set(cls.manifest["jobs"])

    def selected(self, *paths: str) -> set[str]:
        result = select_jobs(paths, self.manifest)
        return {job for job, enabled in result["jobs"].items() if enabled}

    def test_empty_diff_fails_open(self) -> None:
        result = select_jobs([], self.manifest)
        self.assertTrue(result["full"])
        self.assertEqual(self.selected(), self.all_jobs)

    def test_forced_run_is_full(self) -> None:
        result = select_jobs(
            ["sync/jukuravi_d0_check.sh"], self.manifest, force_full=True
        )
        self.assertTrue(result["full"])
        self.assertEqual(
            {job for job, enabled in result["jobs"].items() if enabled}, self.all_jobs
        )

    def test_unchanged_sentinel_can_skip_all_lanes(self) -> None:
        result = select_jobs([], self.manifest, force_full=True, skip_all=True)
        self.assertFalse(result["full"])
        self.assertEqual(
            {job for job, enabled in result["jobs"].items() if enabled}, set()
        )
        self.assertTrue(result["skip_reason"])

    def test_unknown_path_fails_open(self) -> None:
        self.assertEqual(self.selected("sync/new_guard.sh"), self.all_jobs)

    def test_shared_hdl_is_full(self) -> None:
        self.assertEqual(self.selected("hdl/juku_top.v"), self.all_jobs)

    def test_control_change_is_full(self) -> None:
        self.assertEqual(self.selected("ci/hdl-ci.json"), self.all_jobs)

    def test_fdc_media_selects_fdc_and_boot(self) -> None:
        self.assertEqual(
            self.selected("media/disks/system.dsk"), {"fdc", "boot"}
        )

    def test_documentation_does_not_force_full(self) -> None:
        result = select_jobs(["sync/README.md"], self.manifest)
        self.assertFalse(result["full"])
        self.assertEqual(self.selected("sync/README.md"), set())
        self.assertEqual(
            self.selected("spinoffs/jukuravi/network-rom/README.md"), set()
        )

    def test_documentation_does_not_expand_a_scoped_change(self) -> None:
        self.assertEqual(
            self.selected("sync/fdc_check.sh", "docs/new-note.md"),
            {"fdc", "boot"},
        )

    def test_generated_video_document_selects_its_guard(self) -> None:
        self.assertEqual(
            self.selected("docs/video-physical-probes.md"), {"subsystems"}
        )

    def test_non_hdl_host_guard_does_not_start_hdl_lanes(self) -> None:
        self.assertEqual(self.selected("sync/jukuhost_linux_check.sh"), set())

    def test_network_test_selects_network_lane(self) -> None:
        self.assertEqual(
            self.selected("tests/network_first_rom_abi_test.py"), {"network-rom"}
        )
        self.assertEqual(self.selected("host/src/jukuhost_core.c"), {"network-rom"})

    def test_generated_fabrication_output_does_not_start_hdl(self) -> None:
        self.assertEqual(self.selected("fab/minimal-vga/revb/io.kicad_pcb"), set())

    def test_shared_jukuravi_submodule_selects_all_jukuravi_lanes(self) -> None:
        self.assertEqual(
            self.selected("third_party/juku-common"),
            {"jukuravi-d0", "network-rom", "jukuravi-regression"},
        )

    def test_main_board_change_is_full(self) -> None:
        self.assertEqual(self.selected("kicad/juku.board.json"), self.all_jobs)

    def test_jukuravi_lanes_are_independent(self) -> None:
        self.assertEqual(
            self.selected("tests/jukuravi_d0_alive_test.py"), {"jukuravi-d0"}
        )
        self.assertEqual(
            self.selected("spinoffs/jukuravi/network-rom/boot.asm"),
            {"jukuravi-d0", "network-rom", "jukuravi-regression"},
        )
        self.assertEqual(
            self.selected("tests/jukuravi_t31_low4k_test.py"),
            {"jukuravi-regression"},
        )

    def test_jukuravi_product_change_runs_all_jukuravi_lanes(self) -> None:
        self.assertEqual(
            self.selected("spinoffs/jukuravi/firmware/build_d0_alive.py"),
            {"jukuravi-d0", "network-rom", "jukuravi-regression"},
        )

    def test_jukuravi_shared_change_selects_all_jukuravi_lanes(self) -> None:
        self.assertEqual(
            self.selected("spinoffs/jukuravi/protocol.py"),
            {"jukuravi-d0", "network-rom", "jukuravi-regression"},
        )

    def test_revb_change_selects_both_video_lanes(self) -> None:
        self.assertEqual(
            self.selected("spinoffs/minimal-vga/hdl/revb/video.v"),
            {"minimal-vga", "revb-ttl-boot"},
        )

    def test_lvs_input_stays_inside_video_and_lvs_lanes(self) -> None:
        self.assertEqual(
            self.selected("spinoffs/minimal-vga/sync/revb_mem_map.json"),
            {"lvs", "minimal-vga", "revb-ttl-boot"},
        )

    def test_multi_area_change_selects_union(self) -> None:
        self.assertEqual(
            self.selected(
                "sync/fdc_check.sh", "spinoffs/minimal-vga/sim/vjuga_boot_check.sh"
            ),
            {"fdc", "boot", "minimal-vga"},
        )

    def test_one_unknown_path_makes_multi_area_change_full(self) -> None:
        self.assertEqual(
            self.selected("sync/fdc_check.sh", "tests/new_unknown_test.py"),
            self.all_jobs,
        )

    def test_every_manifest_entrypoint_selects_its_owner(self) -> None:
        for job, data in self.manifest["jobs"].items():
            for entrypoint in data["entrypoints"]:
                with self.subTest(job=job, entrypoint=entrypoint):
                    self.assertIn(job, self.selected(entrypoint))


if __name__ == "__main__":
    unittest.main()
