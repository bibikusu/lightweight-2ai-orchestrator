from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from orchestration.queue import QueueEngine, QueueItem, QueueStore

from orchestration.scheduler.plan_loader import ScheduledPlan, SchedulerPlanLoader

JST = ZoneInfo("Asia/Tokyo")


def _parse_now_arg(raw: str) -> datetime:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=JST)
    return dt.astimezone(JST)


class CronRunner:
    def __init__(
        self,
        plan_loader: SchedulerPlanLoader,
        *,
        queue_store: QueueStore | None = None,
    ) -> None:
        self._plan_loader = plan_loader
        self._queue_store = queue_store if queue_store is not None else QueueStore()

    def tick(self, now: datetime, *, force_plan_id: str | None = None) -> list[QueueItem]:
        """
        now: JST の現在時刻(aware datetime)
        戻り値: この tick で enqueue + dispatch + run された QueueItem のリスト

        force_plan_id が指定されたときは、その plan のみ時刻判定をバイパスして実行する。
        """
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        now_jst = now.astimezone(JST)

        qconf, plans = self._plan_loader.load()
        engine = QueueEngine(
            self._queue_store,
            qconf.registry_path,
            qconf.policy_path,
        )
        ran: list[QueueItem] = []
        for plan in plans:
            if force_plan_id is not None:
                if plan.id != force_plan_id:
                    continue
            elif not self.plan_matches(plan, now_jst):
                continue
            ran.extend(self._run_plan(engine, plan))
        return ran

    @staticmethod
    def plan_matches(plan: ScheduledPlan, now: datetime) -> bool:
        """
        plan.weekday が None のとき: hour と minute の両方が一致するかのみ判定
        plan.weekday が 1-7 のとき: ISO weekday(now.isoweekday())と hour/minute が全て一致
        plan.enabled == False のとき: 常に False
        """
        if not plan.enabled:
            return False
        now_jst = now.astimezone(JST)
        if now_jst.hour != plan.hour or now_jst.minute != plan.minute:
            return False
        if plan.weekday is None:
            return True
        return int(now_jst.isoweekday()) == int(plan.weekday)

    @staticmethod
    def _run_plan(queue: QueueEngine, plan: ScheduledPlan) -> list[QueueItem]:
        """plan.sessions を順に enqueue し、その後 dispatch_ready と run_next を尽きるまで実行。"""
        out: list[QueueItem] = []
        for sess in plan.sessions:
            queue.enqueue(sess.session_id, sess.project_id)
        queue.dispatch_ready()
        while True:
            item = queue.run_next()
            if item is None:
                break
            out.append(item)
        return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Scheduler cron runner")
    parser.add_argument(
        "--now",
        type=str,
        default=None,
        help="Override current time as ISO8601 string (JST). Default: datetime.now(JST)",
    )
    parser.add_argument(
        "--plan-id",
        type=str,
        default=None,
        help="Run a specific plan by id, bypassing time match",
    )
    args = parser.parse_args()

    if args.now:
        now = _parse_now_arg(args.now)
    else:
        now = datetime.now(JST)

    loader = SchedulerPlanLoader()
    runner = CronRunner(loader)
    runner.tick(now, force_plan_id=args.plan_id)


if __name__ == "__main__":
    main()
