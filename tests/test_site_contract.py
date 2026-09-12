from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
STYLES = ROOT / "styles.css"
SCRIPT = ROOT / "script.js"
MANIFEST = ROOT / "assets" / "manifest.json"


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.classes: list[set[str]] = []
        self.images: list[str] = []
        self.links: list[dict[str, str | None]] = []
        self.footer_count = 0
        self.lang: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "html":
            self.lang = data.get("lang")
        if data.get("id"):
            self.ids.add(str(data["id"]))
        class_names = set((data.get("class") or "").split())
        if class_names:
            self.classes.append(class_names)
        if tag == "img" and data.get("src"):
            self.images.append(str(data["src"]))
        if tag == "a":
            self.links.append(data)
        if tag == "footer":
            self.footer_count += 1


class LaCalabazaContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not INDEX.exists():
            raise AssertionError("index.html must exist")
        cls.html = INDEX.read_text(encoding="utf-8")
        cls.css = STYLES.read_text(encoding="utf-8")
        cls.js = SCRIPT.read_text(encoding="utf-8")
        cls.parser = SiteParser()
        cls.parser.feed(cls.html)

    def test_document_language_and_required_sections(self) -> None:
        self.assertEqual(self.parser.lang, "en")
        expected = {"home", "trend", "cats", "videos", "how-to-buy"}
        self.assertTrue(expected.issubset(self.parser.ids))
        self.assertEqual(self.parser.footer_count, 1)

    def test_brand_and_network_copy_are_present(self) -> None:
        for phrase in (
            "LA CALABAZA",
            "BUILT FOR BNB CHAIN",
            "Three kittens. One beat. Zero explanation.",
            "HOW THREE KITTENS TOOK OVER THE INTERNET",
            "CUTE. STRANGE. INSTANTLY REMIXABLE.",
            "THE INTERNET KEEPS DANCING",
            "BORN TO DANCE ON BNB CHAIN.",
        ):
            self.assertIn(phrase, self.html)

    def test_network_copy_does_not_claim_an_unverified_live_state(self) -> None:
        self.assertNotIn("LIVE ON BNB CHAIN", self.html)
        self.assertNotIn("Launch details pending verification", self.html)
        self.assertNotIn("Contract pending", self.html)
        self.assertGreaterEqual(self.html.count("SOON"), 2)

    def test_wallet_connection_and_fake_contract_are_absent(self) -> None:
        self.assertNotIn("connect wallet", self.html.lower())
        self.assertNotRegex(self.html, r"0x[a-fA-F0-9]{40}")
        self.assertNotIn("Contract pending", self.html)
        self.assertIn('data-config="contractAddress"', self.html)

    def test_exactly_three_vertical_tiktok_cards_exist(self) -> None:
        cards = [classes for classes in self.parser.classes if "video-card" in classes]
        self.assertEqual(len(cards), 3)
        self.assertRegex(self.css, r"\.video-card\s*\{[^}]*aspect-ratio:\s*9\s*/\s*16")
        video_tags = re.findall(r'<video\b[^>]*class="video-media"[^>]*>', self.html)
        self.assertEqual(len(video_tags), 3)
        for number, tag in zip(("01", "02", "03"), video_tags, strict=True):
            self.assertIn(f'src="./assets/video-{number}.mp4"', tag)
            self.assertIn("controls", tag)
            self.assertIn("playsinline", tag)
            self.assertTrue((ROOT / "assets" / f"video-{number}.mp4").is_file())
        self.assertNotIn("Real TikTok links pending", self.html)
        self.assertNotIn("Watch on TikTok", self.html)

    def test_video_one_is_the_original_meowtakeover_post(self) -> None:
        original_url = "https://www.tiktok.com/@meowtakeover/video/7678841126555553042"
        self.assertIn("ORIGINAL · @MEOWTAKEOVER", self.html)
        self.assertRegex(
            self.html,
            rf'<a\b[^>]*href="{re.escape(original_url)}"[^>]*>ORIGINAL · @MEOWTAKEOVER ↗</a>',
        )
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        video = next(item for item in manifest["assets"] if item["file"] == "video-01.mp4")
        poster = next(item for item in manifest["assets"] if item["file"] == "tiktok-poster-01.png")
        self.assertEqual(video["source"], "Download (3).mp4")
        self.assertEqual(poster["source"], "Download (3).mp4")

    def test_story_credits_meowtakeover_and_links_primary_sources(self) -> None:
        original_url = "https://www.tiktok.com/@meowtakeover/video/7678841126555553042"
        profile_url = "https://www.tiktok.com/@meowtakeover"
        know_your_meme_url = "https://knowyourmeme.com/memes/three-kittens-dancing-the-dark-triad"
        self.assertIn("On June 28, 2026", self.html)
        self.assertIn("the original three-kitten routine", self.html)
        self.assertIn("green-screen edits, remixes and recreations", self.html)
        self.assertIn(f'href="{profile_url}"', self.html)
        self.assertGreaterEqual(self.html.count(f'href="{original_url}"'), 3)
        self.assertIn(f'href="{original_url}" target="_blank" rel="noreferrer">Source 01 ↗</a>', self.html)
        self.assertIn(f'href="{know_your_meme_url}" target="_blank" rel="noreferrer">Source 02 ↗</a>', self.html)
        self.assertNotIn("canal44.com", self.html)
        self.assertRegex(
            self.html,
            rf'<a\b[^>]*href="{re.escape(original_url)}"[^>]*>TikTok ↗</a>',
        )

    def test_every_local_image_exists_and_has_accessibility_text(self) -> None:
        self.assertGreaterEqual(len(self.parser.images), 4)
        for src in self.parser.images:
            self.assertFalse(src.startswith(("http://", "https://")))
            self.assertTrue((ROOT / src).is_file(), f"Missing local asset: {src}")
        image_tags = re.findall(r"<img\b[^>]*>", self.html, flags=re.IGNORECASE)
        self.assertTrue(all(re.search(r"\balt=", tag, flags=re.IGNORECASE) for tag in image_tags))

    def test_external_actions_are_disabled_until_real_urls_exist(self) -> None:
        pending = [link for link in self.parser.links if link.get("data-pending") == "true"]
        self.assertGreaterEqual(len(pending), 4)
        for link in pending:
            self.assertEqual(link.get("aria-disabled"), "true")
            if link.get("data-link") in {"buy", "x"}:
                self.assertIsNone(link.get("href"))

    def test_public_launch_config_wires_ca_x_and_buy_everywhere(self) -> None:
        self.assertIn('<script src="./runtime-config.js"></script>', self.html)
        self.assertIn('<script type="module" src="./public-config.mjs"></script>', self.html)
        self.assertGreaterEqual(self.html.count('data-link="buy"'), 3)
        self.assertGreaterEqual(self.html.count('data-link="x"'), 3)
        self.assertEqual(self.html.count('data-config="contractAddress"'), 2)
        self.assertIn('data-copy-contract', self.html)
        self.assertIn('navigator.clipboard.writeText', self.js)

    def test_motion_and_audio_require_user_control(self) -> None:
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn('id="dance-toggle"', self.html)
        self.assertIn('id="motion-toggle"', self.html)
        self.assertIn('aria-pressed="false"', self.html)
        self.assertIn("AudioContext", self.js)
        self.assertIn("audioTransitioning", self.js)
        self.assertIn("catch (error)", self.js)
        self.assertIn("motion-paused", self.js)
        self.assertIn(".motion-paused .ticker-track", self.css)
        self.assertNotIn("autoplay", self.html.lower())

    def test_ticker_uses_two_complete_sequences_for_a_gapless_loop(self) -> None:
        sequences = re.findall(
            r'<div class="ticker-sequence">([\s\S]*?)</div>',
            self.html,
        )
        self.assertEqual(len(sequences), 2)
        normalized = [re.sub(r"\s+", "", sequence) for sequence in sequences]
        self.assertEqual(normalized[0], normalized[1])
        for phrase in ("MEOW", "DANCE", "REPEAT", "$CALABAZA", "BNB CHAIN"):
            self.assertGreaterEqual(sequences[0].count(f"<span>{phrase}</span>"), 3)
        self.assertRegex(
            self.css,
            r"\.ticker-sequence\s*\{[^}]*flex:\s*0\s+0\s+auto[^}]*min-width:\s*100vw",
        )
        self.assertRegex(
            self.css,
            r"@keyframes ticker\s*\{[^}]*translate3d\(-50%,\s*0,\s*0\)",
        )

    def test_reference_hero_fits_viewport_without_clipped_cat_layers(self) -> None:
        self.assertRegex(self.html, r'<h1\b[^>]*id="hero-title"[^>]*>\s*LA CALABAZA\s*</h1>')
        self.assertIn('class="hero-stage"', self.html)
        self.assertRegex(self.css, r"\.hero-stage\s*\{[^}]*height:\s*100svh")
        self.assertNotIn("data-dance-cat", self.html)
        self.assertNotIn("hero-dance-cat", self.css)
        self.assertIn('class="hero-art" src="./assets/hero-kittens.png"', self.html)
        self.assertIn('class="hero-video-background" src="./assets/hero-background.png"', self.html)
        self.assertIn('id="hero-dance-video"', self.html)
        self.assertIn('src="./assets/hero-dance-alpha.webm"', self.html)
        self.assertIn('poster="./assets/hero-dance-poster.png"', self.html)
        self.assertIn('loop playsinline preload="metadata"', self.html)
        self.assertIn('data-video-state="ready"', self.html)
        for filename in ("hero-background.png", "hero-dance-alpha.webm", "hero-dance-poster.png"):
            self.assertTrue((ROOT / "assets" / filename).is_file())
        self.assertIn("hasApprovedDanceVideo", self.js)
        self.assertIn("danceVideo.play()", self.js)

    def test_hero_video_only_replaces_original_while_dancing(self) -> None:
        self.assertRegex(self.css, r"\.hero-video-background\s*\{[^}]*opacity:\s*0")
        self.assertRegex(self.css, r"\.hero-dance-video\s*\{[^}]*opacity:\s*0[^}]*transform:\s*translate\(2%,\s*10%\)")
        self.assertRegex(
            self.css,
            r"\.has-dance-video\.is-dancing \.hero-art\s*\{[^}]*opacity:\s*0",
        )
        self.assertRegex(
            self.css,
            r"\.has-dance-video\.is-dancing \.hero-video-background,\s*\.has-dance-video\.is-dancing \.hero-dance-video\s*\{[^}]*opacity:\s*1",
        )
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        asset = next(item for item in manifest["assets"] if item["file"] == "hero-dance-alpha.webm")
        self.assertLessEqual(asset["keySettings"]["similarity"], 0.14)
        self.assertLessEqual(asset["keySettings"]["blend"], 0.04)

    def test_hero_wordmark_is_hidden_while_dance_video_is_active(self) -> None:
        self.assertRegex(
            self.css,
            r"\.has-dance-video\.is-dancing \.hero-wordmark\s*\{[^}]*opacity:\s*0[^}]*visibility:\s*hidden",
        )

    def test_dance_video_resets_to_the_beginning_when_paused(self) -> None:
        start = self.js.index("async function stopDance")
        end = self.js.index('danceToggle?.addEventListener("click"', start)
        stop_dance = self.js[start:end]
        self.assertIn("danceVideo?.pause();", stop_dance)
        self.assertIn("danceVideo.currentTime = 0;", stop_dance)
        self.assertLess(stop_dance.index("danceVideo?.pause();"), stop_dance.index("danceVideo.currentTime = 0;"))

    def test_hero_video_uses_the_latest_corrected_audio_source(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        video = next(item for item in manifest["assets"] if item["file"] == "hero-dance-alpha.webm")
        poster = next(item for item in manifest["assets"] if item["file"] == "hero-dance-poster.png")
        self.assertEqual(video["source"], "2026-09-11 16-45-29.mp4")
        self.assertEqual(poster["source"], "2026-09-11 16-45-29.mp4")

    def test_hero_wordmark_is_legible_without_decorative_orbit_lines(self) -> None:
        self.assertNotIn("hero-orbit", self.html)
        self.assertNotIn(".hero-orbit", self.css)
        self.assertNotIn(".orbit-one", self.css)
        self.assertNotIn(".orbit-two", self.css)
        title_rules = re.findall(r"\.hero-title\s*\{([^}]*)\}", self.css)
        self.assertGreaterEqual(len(title_rules), 1)
        self.assertTrue(all("scaleX" not in rule for rule in title_rules))
        self.assertTrue(any("-webkit-text-stroke" in rule for rule in title_rules))

    def test_dance_animation_does_not_depend_on_synthetic_audio(self) -> None:
        start = self.js.index("async function startDance")
        audio_setup = self.js.index("const AudioContextClass", start)
        support_check = self.js.index("if (!AudioContextClass", audio_setup)
        visual_starts = [match.start() for match in re.finditer(r"setDanceUi\(true\)", self.js)]
        self.assertTrue(any(audio_setup < position < support_check for position in visual_starts))

    def test_reference_hero_has_compact_character_strip_without_contract_bar(self) -> None:
        self.assertIn('class="cats-section hero-character-strip"', self.html)
        self.assertIn("hero-character-grid", self.css)
        self.assertNotIn('id="hero-contract-bar"', self.html)
        self.assertNotIn("0x… pending verification", self.html)
        self.assertNotIn("hero-contract-bar", self.css)
        self.assertIn("GOOD CATS", self.html)
        self.assertIn("DANCE TOGETHER", self.html)

    def test_character_cards_use_three_dedicated_assets(self) -> None:
        expected = (
            "./assets/character-shy-face.png",
            "./assets/character-drama-hat-face.png",
            "./assets/character-brain-face.png",
        )
        for src in expected:
            self.assertIn(src, self.html)
            self.assertTrue((ROOT / src).is_file(), f"Missing dedicated card asset: {src}")
        self.assertEqual(self.html.count("character-portrait--face"), 3)
        self.assertIn(".character-portrait--face", self.css)
        self.assertNotIn("width: 150%", self.css)
        self.assertRegex(self.css, r"\.character-portrait--face\s*\{[^}]*width:\s*58%[^}]*height:\s*auto")
        self.assertRegex(
            self.html,
            r'<img\b[^>]*src="\./assets/character-drama-hat-face\.png"[^>]*alt="[^"]*black wide-brim hat[^"]*"',
        )

    def test_lower_page_matches_compact_reference_composition(self) -> None:
        for class_name in (
            "story-art",
            "story-content",
            "viral-grid",
            "videos-layout",
            "launch-footer",
        ):
            self.assertIn(class_name, self.html)
        self.assertNotIn('class="remix-section"', self.html)
        self.assertNotIn('class="buy-section"', self.html)
        self.assertIn('id="memes"', self.html)
        self.assertIn('id="how-to-buy"', self.html)

    def test_story_illustration_is_original_16_9_fan_art(self) -> None:
        self.assertRegex(
            self.html,
            r'(?i)<img\b[^>]*src="\./assets/story-kittens-stage\.png"[^>]*alt="[^"]*fan-art illustration[^"]*"',
        )
        self.assertRegex(
            self.html,
            r'(?i)<img\b[^>]*src="\./assets/story-kittens-stage\.png"[^>]*alt="[^"]*night street[^"]*"',
        )
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        asset = next(item for item in manifest["assets"] if item["file"] == "story-kittens-stage.png")
        self.assertIn("fan-art", asset["role"].lower())
        self.assertIn("night street", asset["role"].lower())
        self.assertNotIn("pumpkin", asset["role"].lower())
        width, height = asset["dimensions"]
        self.assertAlmostEqual(width / height, 16 / 9, places=2)
        self.assertRegex(
            self.html,
            r'<section class="story-section"[^>]*>\s*<figure class="story-art">[\s\S]*?</figure>\s*<div class="container story-grid">',
        )
        self.assertRegex(
            self.css,
            r"\.story-section\s*\{[^}]*position:\s*relative[^}]*isolation:\s*isolate",
        )
        self.assertRegex(self.css, r"\.story-art\s*\{[^}]*position:\s*absolute[^}]*inset:\s*0")
        self.assertRegex(self.css, r"\.story-art img\s*\{[^}]*object-fit:\s*cover")
        self.assertRegex(self.css, r"\.story-grid\s*\{[^}]*place-items:\s*center")
        self.assertRegex(self.css, r"\.story-content\s*\{[^}]*text-align:\s*center")

    def test_mobile_story_title_keeps_readable_line_spacing(self) -> None:
        mobile = re.search(r"@media\s*\(max-width:\s*700px\)\s*\{([\s\S]*)\}\s*$", self.css)
        self.assertIsNotNone(mobile)
        mobile_css = mobile.group(1)
        self.assertRegex(
            mobile_css,
            r"\.story-content h2\s*\{[^}]*font-size:\s*clamp\(3rem,\s*15vw,\s*4\.4rem\)[^}]*line-height:\s*\.88",
        )

    def test_project_has_no_telegram_link(self) -> None:
        self.assertNotIn("telegram", self.html.lower())

    def test_basic_accessibility_hooks_exist(self) -> None:
        self.assertIn('class="skip-link"', self.html)
        self.assertIn('aria-label="Primary navigation"', self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('id="visual-status"', self.html)
        self.assertIn('role="status"', self.html)
        self.assertRegex(self.html, r'<p\s+class="sr-only"\s+id="visual-status"')
        self.assertNotIn("Launch details pending verification", self.html)
        self.assertIn(".sr-only", self.css)
        self.assertIn(":focus-visible", self.css)

    def test_footer_wordmark_uses_layout_safe_sizing(self) -> None:
        self.assertIn('class="site-footer launch-footer"', self.html)
        self.assertRegex(
            self.html,
            r'<div class="footer-wordmark"[^>]*>\s*<span>LA</span>\s*<span>CALABAZA</span>\s*</div>',
        )
        self.assertRegex(self.css, r"\.footer-wordmark\s*\{[^}]*display:\s*grid")
        self.assertRegex(self.css, r"\.footer-wordmark\s*\{[^}]*font-size:\s*clamp\([^}]*7vw")
        self.assertRegex(self.css, r"\.footer-wordmark\s*\{[^}]*line-height:\s*\.82")
        self.assertRegex(self.css, r"\.footer-wordmark span:first-child\s*\{[^}]*font-size:\s*\.58em")
        self.assertRegex(self.css, r"\.footer-wordmark span:last-child\s*\{[^}]*line-height:\s*\.82")
        self.assertNotRegex(self.css, r"\.footer-wordmark\s*\{[^}]*transform:\s*scaleX")
        mobile_footer = re.search(r"@media\s*\(max-width:\s*700px\)\s*\{([\s\S]*)\}\s*$", self.css)
        self.assertIsNotNone(mobile_footer)
        mobile_css = mobile_footer.group(1)
        self.assertRegex(mobile_css, r"\.footer-wordmark\s*\{[^}]*15vw")
        self.assertRegex(mobile_css, r"\.launch-layout\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)")
        self.assertRegex(mobile_css, r"\.launch-info\s*\{[^}]*width:\s*100%")
        self.assertRegex(mobile_css, r"\.launch-actions\s*\{[^}]*display:\s*flex")
        self.assertRegex(mobile_css, r"\.footer-contract\s*\{[^}]*flex:\s*1\s+1\s+0")
        self.assertRegex(mobile_css, r"\.footer-contract button\s*\{[^}]*display:\s*none")

    def test_requested_footer_disclaimers_are_removed(self) -> None:
        self.assertNotIn(
            "No wallet connection. Always verify the official contract before using any third-party service.",
            self.html,
        )
        self.assertNotIn("For entertainment only. Always verify the contract address.", self.html)
        self.assertNotIn("launch-disclaimer", self.html)
        self.assertNotIn(".launch-disclaimer", self.css)

    def test_mobile_navigation_and_memes_destinations_exist(self) -> None:
        self.assertIn('id="mobile-nav-toggle"', self.html)
        self.assertIn('aria-controls="mobile-nav"', self.html)
        self.assertIn('id="mobile-nav"', self.html)
        self.assertGreaterEqual(self.html.count('href="#memes">Memes'), 2)

    def test_navbar_stays_visible_and_gains_background_after_half_the_hero(self) -> None:
        self.assertRegex(self.css, r"\.site-header\s*\{[^}]*position:\s*fixed")
        self.assertRegex(self.css, r"\.site-header\.is-scrolled\s*\{[^}]*background:[^}]*backdrop-filter:\s*blur")
        self.assertRegex(self.css, r"\[id\]\s*\{[^}]*scroll-margin-top:")
        self.assertIn("hero.offsetHeight * 0.5", self.js)
        self.assertIn('window.addEventListener("scroll"', self.js)
        self.assertIn("{ passive: true }", self.js)

    def test_navbar_places_x_next_to_buy_and_moves_launch_links_into_mobile_menu(self) -> None:
        self.assertIn('class="header-actions"', self.html)
        self.assertIn('class="header-x pending-action"', self.html)
        self.assertGreaterEqual(self.html.count('class="mobile-launch-link pending-action"'), 2)
        self.assertRegex(self.css, r"@media\s*\(max-width:\s*700px\)[\s\S]*?\.header-actions\s*\{[^}]*display:\s*none")

    def test_mobile_header_and_hero_ctas_stay_inside_the_viewport(self) -> None:
        mobile = re.search(r"@media\s*\(max-width:\s*700px\)\s*\{([\s\S]*)\}\s*$", self.css)
        self.assertIsNotNone(mobile)
        mobile_css = mobile.group(1)
        self.assertRegex(mobile_css, r"\.site-header\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+auto")
        self.assertRegex(mobile_css, r"\.mobile-nav-toggle\s*\{[^}]*grid-column:\s*2")
        self.assertRegex(mobile_css, r"\.hero-actions\s*\{[^}]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\)")
        self.assertRegex(mobile_css, r"\.hero-actions \.button\s*\{[^}]*min-width:\s*0")

    def test_reveal_content_is_visible_without_javascript(self) -> None:
        self.assertRegex(self.css, r"\.reveal\s*\{\s*opacity:\s*1;\s*transform:\s*none;")
        self.assertIn(".js-ready .reveal", self.css)

    def test_story_viral_and_character_sections_have_distinct_scroll_reveals(self) -> None:
        character_tags = re.findall(r'<article class="[^"]*character-card[^"]*">', self.html)
        self.assertEqual(len(character_tags), 3)
        self.assertTrue(all("reveal" in tag for tag in character_tags))
        self.assertIn("@keyframes story-drift", self.css)
        self.assertIn(".js-ready .story-content.reveal > *", self.css)
        self.assertIn(".js-ready .story-content.reveal.is-visible > *", self.css)
        self.assertIn(".js-ready .viral-lead.reveal", self.css)
        self.assertRegex(
            self.css,
            r"\.js-ready \.viral-lead\.reveal\s*\{[^}]*opacity:\s*1[^}]*transform:\s*none",
        )
        self.assertIn(".js-ready .viral-lead.reveal > *", self.css)
        self.assertIn(".js-ready .viral-lead.reveal.is-visible > *", self.css)
        self.assertRegex(self.css, r"\.viral-reason\.reveal:nth-child\(2\)\s*\{[^}]*transition-delay:")
        self.assertIn(".js-ready .character-card.reveal", self.css)
        self.assertRegex(self.css, r"\.character-card\.reveal:nth-child\(3\)\s*\{[^}]*transition-delay:")

    def test_local_videos_have_distinct_accessible_names(self) -> None:
        labels = (
            "Play the original @meowtakeover three-kitten video",
            "Play LA CALABAZA video 02",
            "Play LA CALABAZA video 03",
        )
        self.assertEqual(len(labels), len(set(labels)))
        for label in labels:
            self.assertIn(f'aria-label="{label}"', self.html)

    def test_local_favicon_exists(self) -> None:
        self.assertIn('rel="icon" href="./assets/favicon.svg"', self.html)
        self.assertIn('rel="shortcut icon" href="./favicon.ico"', self.html)
        self.assertTrue((ROOT / "assets" / "favicon.svg").is_file())
        self.assertTrue((ROOT / "favicon.ico").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
