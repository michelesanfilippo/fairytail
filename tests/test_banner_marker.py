"""
Tests: banner marker file logic (first-run vs subsequent-run behavior).
Simulates the SKILL.md Step 1 logic in pure Python — no I/O side effects.
"""
import os
import tempfile
import unittest


# ── Pure functions mirroring SKILL.md Step 1 logic ───────────────────────────

def marker_path(claude_dir: str) -> str:
    return os.path.join(claude_dir, "fairytail", ".banner_shown")


def banner_path(claude_dir: str) -> str:
    return os.path.join(claude_dir, "fairytail", "fairytail-ascii.txt")


def should_show_banner(claude_dir: str) -> bool:
    """Returns True if marker file is absent (first run)."""
    return not os.path.exists(marker_path(claude_dir))


def show_banner_and_mark(claude_dir: str, banner_content: str) -> str:
    """
    Simulates Step 1 first-run:
    - Returns banner content to be displayed
    - Creates marker file
    Raises FileNotFoundError if banner file missing.
    """
    bp = banner_path(claude_dir)
    if not os.path.exists(bp):
        raise FileNotFoundError(f"fairytail: banner not found ({bp})")
    with open(bp) as f:
        content = f.read()
    mp = marker_path(claude_dir)
    os.makedirs(os.path.dirname(mp), exist_ok=True)
    with open(mp, "w") as f:
        f.write("1")
    return content


def skip_banner(claude_dir: str) -> None:
    """Simulates Step 1 subsequent-run: does nothing."""
    pass


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestMarkerPath(unittest.TestCase):
    def test_marker_path_structure(self):
        p = marker_path("/home/user/.claude")
        self.assertTrue(p.endswith(".banner_shown"))
        self.assertIn("fairytail", p)

    def test_banner_path_structure(self):
        p = banner_path("/home/user/.claude")
        self.assertTrue(p.endswith("fairytail-ascii.txt"))
        self.assertIn("fairytail", p)


class TestShouldShowBanner(unittest.TestCase):
    def test_no_marker_returns_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(should_show_banner(tmp))

    def test_marker_present_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = marker_path(tmp)
            os.makedirs(os.path.dirname(mp), exist_ok=True)
            with open(mp, "w") as f:
                f.write("1")
            self.assertFalse(should_show_banner(tmp))


class TestShowBannerAndMark(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        ft_dir = os.path.join(self.tmp, "fairytail")
        os.makedirs(ft_dir, exist_ok=True)
        self.banner_file = os.path.join(ft_dir, "fairytail-ascii.txt")
        self.banner_content = "FAIRY TAIL\n...book art...\n"
        with open(self.banner_file, "w") as f:
            f.write(self.banner_content)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_first_run_returns_banner_content(self):
        content = show_banner_and_mark(self.tmp, self.banner_content)
        self.assertEqual(content, self.banner_content)

    def test_first_run_creates_marker(self):
        show_banner_and_mark(self.tmp, self.banner_content)
        self.assertTrue(os.path.exists(marker_path(self.tmp)))

    def test_marker_file_contains_1(self):
        show_banner_and_mark(self.tmp, self.banner_content)
        with open(marker_path(self.tmp)) as f:
            self.assertEqual(f.read(), "1")

    def test_after_first_run_marker_suppresses_banner(self):
        show_banner_and_mark(self.tmp, self.banner_content)
        self.assertFalse(should_show_banner(self.tmp))

    def test_missing_banner_file_raises(self):
        os.remove(self.banner_file)
        with self.assertRaises(FileNotFoundError):
            show_banner_and_mark(self.tmp, "")

    def test_missing_banner_error_message(self):
        os.remove(self.banner_file)
        try:
            show_banner_and_mark(self.tmp, "")
        except FileNotFoundError as e:
            self.assertIn("banner not found", str(e))


class TestFirstRunFlow(unittest.TestCase):
    """End-to-end: first run shows banner + marks; second run skips."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        ft_dir = os.path.join(self.tmp, "fairytail")
        os.makedirs(ft_dir, exist_ok=True)
        with open(os.path.join(ft_dir, "fairytail-ascii.txt"), "w") as f:
            f.write("FAIRY TAIL ASCII\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_first_run_shows_banner(self):
        self.assertTrue(should_show_banner(self.tmp))
        content = show_banner_and_mark(self.tmp, "")
        self.assertIn("FAIRY TAIL", content)

    def test_second_run_skips_banner(self):
        show_banner_and_mark(self.tmp, "")      # first run
        self.assertFalse(should_show_banner(self.tmp))  # second run → skip

    def test_marker_persists_across_calls(self):
        show_banner_and_mark(self.tmp, "")
        for _ in range(5):
            self.assertFalse(should_show_banner(self.tmp))

    def test_removing_marker_resets_to_first_run(self):
        show_banner_and_mark(self.tmp, "")
        os.remove(marker_path(self.tmp))
        self.assertTrue(should_show_banner(self.tmp))  # reinstall simulation


class TestUninstallClearsMarker(unittest.TestCase):
    """Verifies that deleting the marker file (as uninstallers do) resets banner state."""

    def test_delete_marker_resets_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            ft_dir = os.path.join(tmp, "fairytail")
            os.makedirs(ft_dir)
            with open(os.path.join(ft_dir, "fairytail-ascii.txt"), "w") as f:
                f.write("banner")

            # simulate first run
            show_banner_and_mark(tmp, "")
            self.assertFalse(should_show_banner(tmp))

            # simulate uninstall (removes marker)
            os.remove(marker_path(tmp))
            self.assertTrue(should_show_banner(tmp))  # fresh install → shows again


if __name__ == "__main__":
    unittest.main()
