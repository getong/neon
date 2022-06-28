import os
import time
from typing import List

import time
import pytest
from fixtures.benchmark_fixture import MetricReport
from fixtures.compare_fixtures import NeonCompare, PgCompare
from fixtures.pg_stats import PgStatTable

from performance.test_perf_pgbench import get_durations_matrix, get_scales_matrix


def get_seeds_matrix(default: int = 100):
    seeds = os.getenv("TEST_PG_BENCH_SEEDS_MATRIX", default=str(default))
    return list(map(int, seeds.split(",")))


@pytest.mark.parametrize("seed", get_seeds_matrix())
@pytest.mark.parametrize("scale", get_scales_matrix())
@pytest.mark.parametrize("duration", get_durations_matrix(5))
def test_compare_pg_stats_rw_with_pgbench_default(neon_with_baseline: PgCompare,
                                                  seed: int,
                                                  scale: int,
                                                  duration: int,
                                                  pg_stats_rw: List[PgStatTable]):
    env = neon_with_baseline
    # initialize pgbench
    env.pg_bin.run_capture(['pgbench', f'-s{scale}', '-i', env.pg.connstr()])
    env.flush()

    with env.record_pg_stats(pg_stats_rw):
        env.pg_bin.run_capture([
            'pgbench',
            f'-T{duration}',
            f'--random-seed={seed}',
            '-Mprepared',
            '-r',
            env.pg.connstr()
        ])
        env.flush()


@pytest.mark.parametrize("seed", get_seeds_matrix())
@pytest.mark.parametrize("scale", get_scales_matrix())
@pytest.mark.parametrize("duration", get_durations_matrix(5))
def test_compare_pg_stats_wo_with_pgbench_simple_update(neon_with_baseline: PgCompare,
                                                        seed: int,
                                                        scale: int,
                                                        duration: int,
                                                        pg_stats_wo: List[PgStatTable]):
    env = neon_with_baseline
    # initialize pgbench
    env.pg_bin.run_capture(['pgbench', f'-s{scale}', '-i', env.pg.connstr()])
    env.flush()

    with env.record_pg_stats(pg_stats_wo):
        env.pg_bin.run_capture([
            'pgbench',
            '-N',
            f'-T{duration}',
            f'--random-seed={seed}',
            '-r',
            '-Mprepared',
            env.pg.connstr()
        ])
        env.flush()


@pytest.mark.parametrize("seed", get_seeds_matrix())
@pytest.mark.parametrize("scale", get_scales_matrix())
@pytest.mark.parametrize("duration", get_durations_matrix(5))
def test_compare_pg_stats_ro_with_pgbench_select_only(neon_compare: NeonCompare,
                                                      seed: int,
                                                      scale: int,
                                                      duration: int,
                                                      pg_stats_ro: List[PgStatTable]):
    env = neon_compare
    # initialize pgbench
    env.pg_bin.run_capture(['pgbench', f'-s{scale}', '-i', env.pg.connstr()])
    env.flush()

    with env.record_pg_stats(pg_stats_ro):
        env.pg_bin.run_capture([
            'pgbench',
            '-S',
            f'-T{duration}',
            f'--random-seed={seed}',
            '-Mprepared',
            '-r',
            env.pg.connstr()
        ])
        env.flush()


@pytest.mark.parametrize("seed", get_seeds_matrix())
@pytest.mark.parametrize("scale", get_scales_matrix())
@pytest.mark.parametrize("duration", get_durations_matrix(5))
def test_compare_pg_stats_wal_with_pgbench_default(neon_with_baseline: PgCompare,
                                                   seed: int,
                                                   scale: int,
                                                   duration: int,
                                                   pg_stats_wal: List[PgStatTable]):
    env = neon_with_baseline
    # initialize pgbench
    env.pg_bin.run_capture(['pgbench', f'-s{scale}', '-i', env.pg.connstr()])
    env.flush()

    with env.record_pg_stats(pg_stats_wal):
        env.pg_bin.run_capture(
            ['pgbench', f'-T{duration}', f'--random-seed={seed}', '-Mprepared', env.pg.connstr()])
        env.flush()


@pytest.mark.parametrize("duration", get_durations_matrix(30))
def test_compare_pg_stats_wo_with_simple_write(neon_compare: NeonCompare,
                                               duration: int,
                                               pg_stats_wo: List[PgStatTable]):
    env = neon_compare
    with env.pg.connect().cursor() as cur:
        cur.execute(
            "CREATE TABLE foo(key serial primary key, t text default 'foooooooooooooooooooooooooooooooooooooooooooooooooooo')"
        )

    start = time.time()
    with env.record_pg_stats(pg_stats_wo):
        with env.pg.connect().cursor() as cur:
            while time.time() - start < duration:
                cur.execute("INSERT INTO foo SELECT FROM generate_series(1,1000)")
