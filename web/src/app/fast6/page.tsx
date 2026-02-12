import React from 'react';
import Fast6Dashboard from '@/components/fast6/Fast6Dashboard';
import { getLeaderboardServer, getSeasonStatsServer, getRoiTrendsServer, getGamesServer, getPicksServer } from '@/lib/api';
import { getServerToken } from '@/lib/server-token';

export default async function Fast6Page() {
  const currentSeason = process.env.NEXT_PUBLIC_CURRENT_SEASON ? parseInt(process.env.NEXT_PUBLIC_CURRENT_SEASON) : 2024;
  const testUsername = process.env.NEXT_PUBLIC_TEST_USERNAME || 'akursar';

  // Get server-side token
  const token = await getServerToken(testUsername);

  // Fetch data
  const [leaderboardRes, statsRes, trendsRes, gamesRes, picksRes] = await Promise.all([
    getLeaderboardServer(currentSeason, token!),
    getSeasonStatsServer(currentSeason, token!),
    getRoiTrendsServer(currentSeason, token!),
    getGamesServer(currentSeason, token!),
    getPicksServer(token!)
  ]);

  const leaderboard = leaderboardRes.ok ? leaderboardRes.data : [];
  const stats = statsRes.ok ? statsRes.data : null;
  const trends = trendsRes.ok ? trendsRes.data : [];
  const games = gamesRes.ok ? gamesRes.data : [];
  const picks = picksRes.ok ? picksRes.data : [];

  return (
    <Fast6Dashboard
      leaderboard={leaderboard}
      stats={stats}
      trends={trends}
      games={games}
      userPicks={picks}
      authToken={token || undefined}
    />
  );
}
