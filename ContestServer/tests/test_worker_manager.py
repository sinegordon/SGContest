import sys
import unittest
import importlib.util
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "worker" not in sys.modules:
    sys.modules["worker"] = SimpleNamespace(WorkerHandle=object)

MODULE_PATH = PROJECT_ROOT / "services" / "worker_manager.py"
MODULE_SPEC = importlib.util.spec_from_file_location("worker_manager_module", MODULE_PATH)
worker_manager_module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(worker_manager_module)
WorkerManager = worker_manager_module.WorkerManager


class WorkerManagerTests(unittest.TestCase):
    def test_get_message_result_uses_stable_result_id_snapshot(self):
        manager = WorkerManager.__new__(WorkerManager)
        manager.workers = [SimpleNamespace(results={"abc": {"done": True}})]
        manager.added_problems_id_list = ["abc"]

        result, result_id = WorkerManager.get_message_result(manager, "abc")

        self.assertEqual(result, {"done": True})
        self.assertEqual(result_id, "abc")
        self.assertEqual(manager.added_problems_id_list, [])


if __name__ == "__main__":
    unittest.main()
