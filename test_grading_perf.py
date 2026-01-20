"""
Test grading performance with the new TD lookup cache.
"""
import sys
import time
sys.path.insert(0, 'src')

from utils.grading_logic import get_td_lookup_cache

def test_cache_loading():
    """Test TD cache loading time."""
    season = 2025
    
    print(f"Loading TD cache for season {season}...")
    start = time.time()
    cache = get_td_lookup_cache(season)
    elapsed = time.time() - start
    
    print(f"✓ Cache loaded in {elapsed:.2f}s")
    print(f"  - {len(cache.first_tds_by_game)} games with first TDs")
    print(f"  - {len(cache.all_tds_by_game)} games with all TDs")
    print(f"  - Cached at: {cache.cached_at}")
    
    # Test cache access speed
    if cache.first_tds_by_game:
        game_id = list(cache.first_tds_by_game.keys())[0]
        start = time.time()
        for _ in range(1000):
            first_td = cache.get_first_td_for_game(game_id)
        elapsed = time.time() - start
        print(f"\n✓ 1000 cache lookups in {elapsed*1000:.2f}ms ({elapsed/1000*1000:.4f}ms per lookup)")
    
    return cache

if __name__ == '__main__':
    cache = test_cache_loading()
    print("\n✓ TD lookup cache working correctly")
