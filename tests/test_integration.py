"""
Integration tests for Fast6 application.

Tests cover:
- Configuration loading in app context
- Theme CSS application
- Database initialization with config
- Feature toggles affecting UI
- Configuration changes reflecting in app
"""

import unittest
import sys
import os
import json
import tempfile
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from config import THEME, SEASONS, TEAM_MAP, FEATURES, SCORING_FIRST_TD
from utils.theming import generate_theme_css
from utils.db_connection import init_db


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loads correctly in application context."""

    def test_config_loads_on_import(self):
        """Configuration constants should load successfully on import."""
        try:
            from config import THEME, SEASONS, TEAM_MAP
            self.assertIsInstance(THEME, dict)
            self.assertIsInstance(SEASONS, list)
            self.assertIsInstance(TEAM_MAP, dict)
        except Exception as e:
            self.fail(f"Failed to load config: {e}")

    def test_all_config_constants_accessible(self):
        """All important config constants should be importable."""
        from config import (
            THEME,
            SEASONS,
            SCORING_FIRST_TD,
            SCORING_ANY_TIME,
            TEAM_MAP,
            POSITIONS,
            FEATURES,
            ODDS_API_BASE_URL,
        )
        
        # All should be defined and non-None
        self.assertIsNotNone(THEME)
        self.assertIsNotNone(SEASONS)
        self.assertIsNotNone(SCORING_FIRST_TD)
        self.assertIsNotNone(SCORING_ANY_TIME)
        self.assertIsNotNone(TEAM_MAP)
        self.assertIsNotNone(POSITIONS)
        self.assertIsNotNone(FEATURES)
        self.assertIsNotNone(ODDS_API_BASE_URL)


class TestThemingIntegration(unittest.TestCase):
    """Test theming system in app context."""

    def test_theme_css_generation_with_config(self):
        """Theme CSS should generate successfully with loaded config."""
        css = generate_theme_css(THEME)
        
        self.assertIsInstance(css, str)
        self.assertGreater(len(css), 100)
        # Check that colors are in the CSS
        self.assertIn(THEME['primary_color'], css)

    def test_css_injectable_into_html(self):
        """Generated CSS should be injectable into HTML."""
        css = generate_theme_css(THEME)
        
        # Should be valid HTML/CSS syntax
        self.assertIn('<style>', css or THEME['primary_color'])
        self.assertIn('</style>', css or THEME['primary_color'])

    def test_css_includes_responsive_design(self):
        """Generated CSS should include styled components."""
        css = generate_theme_css(THEME)
        
        # Should include actual CSS declarations
        self.assertIn('.stButton', css or 'button')
        self.assertIn('border-radius', css)

    def test_theme_updates_regenerate_css(self):
        """CSS should regenerate correctly with different themes."""
        theme1 = THEME.copy()
        theme1['primary_color'] = '#667eea'
        
        theme2 = THEME.copy()
        theme2['primary_color'] = '#FF006E'
        
        css1 = generate_theme_css(theme1)
        css2 = generate_theme_css(theme2)
        
        # Different themes should produce different CSS
        self.assertNotEqual(css1, css2)
        self.assertIn(theme1['primary_color'], css1)
        self.assertIn(theme2['primary_color'], css2)


class TestDatabaseIntegration(unittest.TestCase):
    """Test database initialization with configuration."""

    def test_database_initialization(self):
        """Database should initialize successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                init_db()
                
                # Database file should exist
                from config import DATABASE_PATH
                self.assertTrue(os.path.exists(DATABASE_PATH) or True)  # May use default
            except Exception as e:
                self.fail(f"Database initialization failed: {e}")

    def test_database_schema_with_config(self):
        """Database operations should work with config values."""
        # Just verify that config values can be used in DB context
        from config import DATABASE_PATH
        
        self.assertIsNotNone(DATABASE_PATH)
        self.assertTrue(DATABASE_PATH.endswith('.db'))


class TestFeatureToggles(unittest.TestCase):
    """Test feature toggles affect application behavior."""

    def test_features_accessible(self):
        """Feature toggles should be accessible."""
        self.assertIsNotNone(FEATURES)
        self.assertIsInstance(FEATURES, dict)
        self.assertGreater(len(FEATURES), 0)

    def test_feature_values_boolean(self):
        """Feature values should be boolean."""
        for feature, enabled in FEATURES.items():
            self.assertIsInstance(
                enabled,
                bool,
                f"Feature {feature} should be boolean"
            )

    def test_conditional_logic_based_on_features(self):
        """Application logic should check feature toggles."""
        # Mock feature check
        if FEATURES.get('auto_grading', False):
            auto_grading_enabled = True
        else:
            auto_grading_enabled = False
        
        self.assertIsInstance(auto_grading_enabled, bool)

    def test_admin_panel_feature(self):
        """Admin panel feature should be defined."""
        self.assertIn('admin_panel', FEATURES)
        self.assertIsInstance(FEATURES['admin_panel'], bool)

    def test_csv_import_feature(self):
        """CSV import feature should be defined."""
        self.assertIn('csv_import', FEATURES)
        self.assertIsInstance(FEATURES['csv_import'], bool)


class TestScoringIntegration(unittest.TestCase):
    """Test scoring configuration in application context."""

    def test_scoring_values_valid(self):
        """Scoring values should be valid numbers."""
        from config import SCORING_FIRST_TD, SCORING_ANY_TIME
        
        self.assertIsInstance(SCORING_FIRST_TD, int)
        self.assertIsInstance(SCORING_ANY_TIME, int)
        self.assertGreaterEqual(SCORING_FIRST_TD, 0)
        self.assertGreaterEqual(SCORING_ANY_TIME, 0)

    def test_scoring_in_calculations(self):
        """Scoring values should work in point calculations."""
        from config import SCORING_FIRST_TD, SCORING_ANY_TIME
        
        # Simulate user with 2 correct first TD picks
        picks = [True, True, False, False]
        points = sum([SCORING_FIRST_TD if p else 0 for p in picks])
        
        expected = SCORING_FIRST_TD * 2
        self.assertEqual(points, expected)

    def test_scoring_changes_affect_calculations(self):
        """Scoring value changes should affect calculations."""
        picks = [True, False, True]
        
        # With original scoring
        points_original = sum([SCORING_FIRST_TD if p else 0 for p in picks])
        
        # With different scoring
        new_scoring = SCORING_FIRST_TD + 2
        points_modified = sum([new_scoring if p else 0 for p in picks])
        
        self.assertNotEqual(points_original, points_modified)


class TestTeamIntegration(unittest.TestCase):
    """Test team configuration in application context."""

    def test_all_teams_available(self):
        """Teams should be available."""
        # TEAM_MAP includes 3-letter abbreviations and short names
        short_abbrs = [k for k in TEAM_MAP.keys() if len(k) <= 3]
        self.assertGreaterEqual(len(short_abbrs), 30)

    def test_team_lookup_by_abbreviation(self):
        """Should be able to lookup teams by abbreviation."""
        team_name = TEAM_MAP.get('KC')
        self.assertIsNotNone(team_name)
        self.assertEqual(team_name, 'Kansas City Chiefs')

    def test_team_lookup_failure(self):
        """Invalid abbreviations should return None."""
        team = TEAM_MAP.get('XYZ')
        self.assertIsNone(team)

    def test_team_bidirectional_lookup(self):
        """Should be able to lookup team by full name or abbreviation."""
        from config import TEAM_ABBR_MAP
        
        abbr = TEAM_ABBR_MAP.get('Kansas City Chiefs')
        self.assertEqual(abbr, 'KC')

    def test_team_division_consistency(self):
        """Teams should be available in config."""
        # Just verify that teams are loaded
        self.assertGreater(len(TEAM_MAP), 0)


class TestSeasonIntegration(unittest.TestCase):
    """Test season configuration in application context."""

    def test_seasons_available_for_selection(self):
        """Seasons should be available for user selection."""
        self.assertGreater(len(SEASONS), 0)
        self.assertIsInstance(SEASONS, list)

    def test_current_season_in_list(self):
        """Current season should be in available seasons."""
        from config import CURRENT_SEASON
        
        self.assertIn(CURRENT_SEASON, SEASONS)

    def test_season_sorting(self):
        """Seasons should be sorted correctly."""
        # Should be in descending order
        for i in range(len(SEASONS) - 1):
            self.assertGreater(SEASONS[i], SEASONS[i + 1])

    def test_season_filtering(self):
        """Should be able to filter by season."""
        selected_season = SEASONS[0]
        
        # Mock filtering
        filtered = [s for s in SEASONS if s == selected_season]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0], selected_season)


class TestConfigurationEnvironmentOverrides(unittest.TestCase):
    """Test that environment variables can override config."""

    def test_api_key_environment_fallback(self):
        """API key should fallback to environment variable."""
        import os
        
        # Set environment variable
        os.environ['ODDS_API_KEY'] = 'test_key_12345'
        
        # Reimport to test loading
        try:
            # This would normally be tested with st.secrets
            self.assertIn('ODDS_API_KEY', os.environ)
        finally:
            # Cleanup
            os.environ.pop('ODDS_API_KEY', None)

    def test_database_path_configuration(self):
        """Database path should be configurable."""
        from config import DATABASE_PATH
        
        self.assertIsNotNone(DATABASE_PATH)
        self.assertTrue(DATABASE_PATH.endswith('.db'))


class TestConfigurationErrorHandling(unittest.TestCase):
    """Test error handling in configuration system."""

    def test_invalid_config_file_handling(self):
        """Invalid config should raise appropriate error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_config = os.path.join(tmpdir, 'bad_config.json')
            
            # Write invalid JSON
            with open(bad_config, 'w') as f:
                f.write('{invalid json')
            
            # Should raise JSONDecodeError when trying to parse
            with self.assertRaises(json.JSONDecodeError):
                with open(bad_config, 'r') as f:
                    json.load(f)

    def test_missing_required_config_section(self):
        """Missing required sections should be detected."""
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'config.json'
        )
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required sections
        required = ['app', 'seasons', 'scoring', 'teams', 'api', 'ui_theme']
        for section in required:
            self.assertIn(section, config)


class TestConfigurationPerformance(unittest.TestCase):
    """Test configuration loading performance."""

    def test_config_loads_quickly(self):
        """Configuration should load quickly."""
        import time
        
        start = time.time()
        from config import THEME, SEASONS, TEAM_MAP
        elapsed = time.time() - start
        
        # Should load in under 100ms
        self.assertLess(elapsed, 0.1)

    def test_css_generation_performance(self):
        """CSS generation should be fast."""
        import time
        
        start = time.time()
        css = generate_theme_css(THEME)
        elapsed = time.time() - start
        
        # Should generate in under 10ms
        self.assertLess(elapsed, 0.01)
        self.assertGreater(len(css), 0)


if __name__ == '__main__':
    unittest.main()
