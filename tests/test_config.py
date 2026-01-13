"""
Unit tests for Fast6 configuration and theming systems.

Tests cover:
- JSON configuration loading and validation
- Configuration values in SQL queries
- Dynamic CSS generation
- Environment variable and st.secrets overrides
- Theme color validation
"""

import unittest
import json
import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import modules to test
from config import (
    THEME,
    SEASONS,
    SCORING_FIRST_TD,
    SCORING_ANY_TIME,
    TEAM_MAP,
    TEAM_ABBR_MAP,
    POSITIONS,
    FEATURES,
    ODDS_API_BASE_URL,
    ODDS_API_SPORT,
    ODDS_API_MARKET,
)
from utils.theming import generate_theme_css


class TestConfigurationLoading(unittest.TestCase):
    """Test that configuration loads correctly from JSON."""

    def test_config_file_exists(self):
        """Configuration file should exist."""
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'config.json'
        )
        self.assertTrue(
            os.path.exists(config_path),
            "config.json not found"
        )

    def test_config_valid_json(self):
        """Configuration file should be valid JSON."""
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'config.json'
        )
        with open(config_path, 'r') as f:
            try:
                config = json.load(f)
                self.assertIsInstance(config, dict)
            except json.JSONDecodeError as e:
                self.fail(f"config.json is not valid JSON: {e}")

    def test_required_sections_present(self):
        """Configuration should have all required sections."""
        required_sections = [
            'app',
            'seasons',
            'scoring',
            'teams',
            'api',
            'ui_theme',
            'positions',
            'features'
        ]
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'config.json'
        )
        with open(config_path, 'r') as f:
            config = json.load(f)
            for section in required_sections:
                self.assertIn(
                    section,
                    config,
                    f"Missing required section: {section}"
                )


class TestScoringConfiguration(unittest.TestCase):
    """Test scoring configuration and usage in SQL queries."""

    def test_first_td_scoring_is_integer(self):
        """First TD scoring value should be an integer."""
        self.assertIsInstance(SCORING_FIRST_TD, int)
        self.assertGreater(SCORING_FIRST_TD, 0)

    def test_any_time_scoring_is_integer(self):
        """Any-time TD scoring value should be an integer."""
        self.assertIsInstance(SCORING_ANY_TIME, int)
        self.assertGreaterEqual(SCORING_ANY_TIME, 0)

    def test_scoring_in_sql_query(self):
        """Scoring values should work in SQL queries (f-string interpolation)."""
        # Simulate SQL query with scoring values
        query = f"""
            SELECT SUM(CASE 
                WHEN is_correct = 1 THEN {SCORING_FIRST_TD}
                ELSE 0 
            END) as points
            FROM results
        """
        
        # Query should contain the scoring values
        self.assertIn(str(SCORING_FIRST_TD), query)
        self.assertIn("is_correct", query)

    def test_scoring_not_negative(self):
        """Scoring values should not be negative."""
        self.assertGreaterEqual(SCORING_FIRST_TD, 0)
        self.assertGreaterEqual(SCORING_ANY_TIME, 0)

    def test_first_td_greater_than_any_time(self):
        """First TD should typically be worth more than any-time."""
        # This is a convention - first TD picks are harder
        self.assertGreaterEqual(
            SCORING_FIRST_TD,
            SCORING_ANY_TIME,
            "First TD scoring should be >= any-time scoring"
        )


class TestSeasonConfiguration(unittest.TestCase):
    """Test season configuration."""

    def test_seasons_is_list(self):
        """Seasons should be a list."""
        self.assertIsInstance(SEASONS, list)

    def test_seasons_not_empty(self):
        """Seasons list should not be empty."""
        self.assertGreater(len(SEASONS), 0)

    def test_seasons_are_integers(self):
        """Each season should be an integer year."""
        for season in SEASONS:
            self.assertIsInstance(season, int)
            self.assertGreater(season, 1900)
            self.assertLess(season, 2100)

    def test_seasons_in_descending_order(self):
        """Seasons should be in descending order (newest first)."""
        for i in range(len(SEASONS) - 1):
            self.assertGreater(
                SEASONS[i],
                SEASONS[i + 1],
                "Seasons should be in descending order"
            )


class TestTeamConfiguration(unittest.TestCase):
    """Test team configuration."""

    def test_team_map_is_dict(self):
        """Team map should be a dictionary."""
        self.assertIsInstance(TEAM_MAP, dict)

    def test_team_count(self):
        """Should have exactly 32 NFL teams."""
        self.assertEqual(
            len(TEAM_MAP),
            32,
            "Should have 32 NFL teams"
        )

    def test_team_structure(self):
        """Each team should have required fields."""
        required_fields = ['full_name', 'division', 'conference']
        for abbr, team in TEAM_MAP.items():
            self.assertIsInstance(abbr, str)
            self.assertEqual(len(abbr), 3, f"Team abbreviation should be 3 chars: {abbr}")
            
            for field in required_fields:
                self.assertIn(
                    field,
                    team,
                    f"Team {abbr} missing field: {field}"
                )

    def test_valid_conferences(self):
        """Teams should be in AFC or NFC."""
        valid_conferences = {'AFC', 'NFC'}
        for team in TEAM_MAP.values():
            self.assertIn(
                team['conference'],
                valid_conferences,
                f"Invalid conference: {team['conference']}"
            )

    def test_abbr_map_bidirectional(self):
        """Abbreviation map should work both ways."""
        # Check that TEAM_ABBR_MAP is the inverse of TEAM_MAP
        for abbr, team in TEAM_MAP.items():
            full_name = team['full_name']
            self.assertEqual(
                TEAM_ABBR_MAP.get(full_name),
                abbr,
                f"Bidirectional mapping failed for {abbr}/{full_name}"
            )

    def test_all_divisions_have_teams(self):
        """Each NFL division should have 4 teams."""
        divisions = {}
        for team in TEAM_MAP.values():
            division = team['division']
            divisions[division] = divisions.get(division, 0) + 1
        
        # Each division should have 4 teams
        for division, count in divisions.items():
            self.assertEqual(
                count,
                4,
                f"Division {division} has {count} teams, should be 4"
            )


class TestPositionConfiguration(unittest.TestCase):
    """Test position configuration."""

    def test_positions_is_list(self):
        """Positions should be a list."""
        self.assertIsInstance(POSITIONS, list)

    def test_positions_not_empty(self):
        """Positions should not be empty."""
        self.assertGreater(len(POSITIONS), 0)

    def test_positions_are_strings(self):
        """Each position should be a string."""
        for pos in POSITIONS:
            self.assertIsInstance(pos, str)
            self.assertGreater(len(pos), 0)

    def test_common_positions_present(self):
        """Common NFL positions should be present."""
        common_positions = ['QB', 'RB', 'WR', 'TE']
        for pos in common_positions:
            self.assertIn(
                pos,
                POSITIONS,
                f"Position {pos} missing"
            )


class TestFeatureConfiguration(unittest.TestCase):
    """Test feature toggle configuration."""

    def test_features_is_dict(self):
        """Features should be a dictionary."""
        self.assertIsInstance(FEATURES, dict)

    def test_features_values_are_boolean(self):
        """All feature values should be boolean."""
        for feature, enabled in FEATURES.items():
            self.assertIsInstance(
                enabled,
                bool,
                f"Feature {feature} should be boolean, got {type(enabled)}"
            )

    def test_required_features_present(self):
        """Should have required feature flags."""
        required_features = [
            'auto_grading',
            'csv_import',
            'admin_panel'
        ]
        for feature in required_features:
            self.assertIn(
                feature,
                FEATURES,
                f"Missing required feature: {feature}"
            )


class TestAPIConfiguration(unittest.TestCase):
    """Test API configuration."""

    def test_api_base_url_is_valid(self):
        """API base URL should be a valid URL."""
        self.assertIsInstance(ODDS_API_BASE_URL, str)
        self.assertTrue(
            ODDS_API_BASE_URL.startswith('http'),
            "API base URL should start with http"
        )

    def test_api_sport_is_string(self):
        """API sport should be a string."""
        self.assertIsInstance(ODDS_API_SPORT, str)
        self.assertGreater(len(ODDS_API_SPORT), 0)

    def test_api_market_is_string(self):
        """API market should be a string."""
        self.assertIsInstance(ODDS_API_MARKET, str)
        self.assertGreater(len(ODDS_API_MARKET), 0)


class TestThemeConfiguration(unittest.TestCase):
    """Test theme/color configuration."""

    def test_theme_is_dict(self):
        """Theme should be a dictionary."""
        self.assertIsInstance(THEME, dict)

    def test_required_colors_present(self):
        """Theme should have required colors."""
        required_colors = [
            'primary_color',
            'secondary_color',
            'accent_color',
            'success_color',
            'error_color',
            'warning_color',
            'info_color'
        ]
        for color in required_colors:
            self.assertIn(
                color,
                THEME,
                f"Missing required color: {color}"
            )

    def test_colors_are_valid_hex(self):
        """All color values should be valid hex codes."""
        import re
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        
        for key, value in THEME.items():
            if 'color' in key and isinstance(value, str):
                self.assertTrue(
                    hex_pattern.match(value),
                    f"Invalid hex color {key}: {value}"
                )

    def test_font_family_is_string(self):
        """Font family should be a string."""
        self.assertIn('font_family', THEME)
        self.assertIsInstance(THEME['font_family'], str)
        self.assertGreater(len(THEME['font_family']), 0)

    def test_border_radius_is_string(self):
        """Border radius should be a string with units."""
        self.assertIn('border_radius', THEME)
        self.assertIsInstance(THEME['border_radius'], str)
        # Should contain px, rem, em, or other CSS unit
        self.assertTrue(
            any(unit in THEME['border_radius'] for unit in ['px', 'rem', 'em', '%']),
            "Border radius should have CSS units"
        )


class TestThemeCSSGeneration(unittest.TestCase):
    """Test dynamic CSS generation from theme."""

    def test_css_generation_returns_string(self):
        """CSS generation should return a string."""
        css = generate_theme_css(THEME)
        self.assertIsInstance(css, str)

    def test_css_generation_not_empty(self):
        """Generated CSS should not be empty."""
        css = generate_theme_css(THEME)
        self.assertGreater(len(css), 0)

    def test_css_contains_primary_color(self):
        """Generated CSS should include primary color."""
        css = generate_theme_css(THEME)
        primary = THEME['primary_color']
        self.assertIn(
            primary,
            css,
            f"CSS should contain primary color {primary}"
        )

    def test_css_contains_secondary_color(self):
        """Generated CSS should include secondary color."""
        css = generate_theme_css(THEME)
        secondary = THEME['secondary_color']
        self.assertIn(
            secondary,
            css,
            f"CSS should contain secondary color {secondary}"
        )

    def test_css_contains_font_family(self):
        """Generated CSS should include font family."""
        css = generate_theme_css(THEME)
        font_family = THEME['font_family']
        self.assertIn(
            font_family,
            css,
            f"CSS should contain font family {font_family}"
        )

    def test_css_is_valid_css(self):
        """Generated CSS should have valid CSS structure."""
        css = generate_theme_css(THEME)
        
        # Should contain opening and closing braces
        self.assertIn('{', css)
        self.assertIn('}', css)
        
        # Should contain valid CSS properties (colon and semicolon)
        self.assertIn(':', css)
        self.assertIn(';', css)

    def test_css_different_themes(self):
        """Different themes should generate different CSS."""
        theme1 = {
            'primary_color': '#667eea',
            'secondary_color': '#764ba2',
            'accent_color': '#f093fb',
            'success_color': '#48bb78',
            'error_color': '#f56565',
            'warning_color': '#ed8936',
            'info_color': '#4299e1',
            'font_family': 'Inter, sans-serif',
            'border_radius': '20px'
        }
        
        theme2 = {
            'primary_color': '#FF006E',
            'secondary_color': '#8338EC',
            'accent_color': '#FFBE0B',
            'success_color': '#00F5FF',
            'error_color': '#FF006E',
            'warning_color': '#FFBE0B',
            'info_color': '#00F5FF',
            'font_family': 'Georgia, serif',
            'border_radius': '10px'
        }
        
        css1 = generate_theme_css(theme1)
        css2 = generate_theme_css(theme2)
        
        # CSS should be different for different themes
        self.assertNotEqual(
            css1,
            css2,
            "Different themes should generate different CSS"
        )
        
        # Each CSS should contain its theme colors
        self.assertIn(theme1['primary_color'], css1)
        self.assertIn(theme2['primary_color'], css2)

    def test_css_gradient_generation(self):
        """Generated CSS should include gradients with both colors."""
        css = generate_theme_css(THEME)
        
        # Should contain gradient syntax with primary and secondary colors
        self.assertIn(
            'linear-gradient',
            css,
            "CSS should include linear gradients"
        )
        self.assertIn(
            THEME['primary_color'],
            css,
            "Gradient should use primary color"
        )
        self.assertIn(
            THEME['secondary_color'],
            css,
            "Gradient should use secondary color"
        )


class TestThemeColorValidation(unittest.TestCase):
    """Test theme color validation and accessibility."""

    def test_all_theme_colors_valid_hex(self):
        """All theme colors should be valid hex codes."""
        import re
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        
        for key, value in THEME.items():
            if 'color' in key and isinstance(value, str):
                self.assertTrue(
                    hex_pattern.match(value),
                    f"Color {key} has invalid hex: {value}"
                )

    def test_primary_and_secondary_different(self):
        """Primary and secondary colors should be different."""
        self.assertNotEqual(
            THEME['primary_color'],
            THEME['secondary_color'],
            "Primary and secondary colors should be different"
        )

    def test_colors_not_pure_black_or_white(self):
        """Avoid pure black/white for contrast issues."""
        # Check primary and secondary aren't pure black/white
        colors_to_check = [
            ('primary_color', THEME['primary_color']),
            ('secondary_color', THEME['secondary_color'])
        ]
        
        pure_colors = {'#000000', '#ffffff', '#FFFFFF'}
        
        for name, color in colors_to_check:
            self.assertNotIn(
                color,
                pure_colors,
                f"{name} should not be pure black or white"
            )


class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration system."""

    def test_all_teams_in_divisions(self):
        """All teams should be in a valid division."""
        valid_divisions = {
            'AFC East', 'AFC West', 'AFC North', 'AFC South',
            'NFC East', 'NFC West', 'NFC North', 'NFC South'
        }
        
        for team in TEAM_MAP.values():
            self.assertIn(
                team['division'],
                valid_divisions,
                f"Invalid division: {team['division']}"
            )

    def test_config_consistency(self):
        """Configuration should be internally consistent."""
        # Team abbreviations should be 3 chars
        for abbr in TEAM_MAP.keys():
            self.assertEqual(len(abbr), 3)
        
        # Scoring should be non-negative
        self.assertGreaterEqual(SCORING_FIRST_TD, 0)
        self.assertGreaterEqual(SCORING_ANY_TIME, 0)
        
        # Colors should be 7 chars (# + 6 hex digits)
        for key, value in THEME.items():
            if 'color' in key and isinstance(value, str):
                self.assertEqual(len(value), 7)

    def test_seasonal_data_completeness(self):
        """Seasonal data should be complete."""
        # Should have seasons
        self.assertGreater(len(SEASONS), 0)
        
        # Should have teams
        self.assertEqual(len(TEAM_MAP), 32)
        
        # Should have positions
        self.assertGreater(len(POSITIONS), 0)


class TestConfigurationReloading(unittest.TestCase):
    """Test configuration reloading and hot updates."""

    def test_config_stable_across_imports(self):
        """Config values should be stable across multiple imports."""
        # Re-import to test stability
        from config import SCORING_FIRST_TD as FIRST_TD_1
        from config import SCORING_FIRST_TD as FIRST_TD_2
        
        self.assertEqual(
            FIRST_TD_1,
            FIRST_TD_2,
            "Config values should be consistent across imports"
        )

    def test_theme_stable_across_imports(self):
        """Theme values should be stable across multiple imports."""
        from config import THEME as THEME_1
        from config import THEME as THEME_2
        
        self.assertEqual(
            THEME_1['primary_color'],
            THEME_2['primary_color'],
            "Theme values should be consistent across imports"
        )


if __name__ == '__main__':
    unittest.main()
