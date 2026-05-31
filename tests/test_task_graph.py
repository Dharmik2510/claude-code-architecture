"""Pattern 7 — file-based task dependency graph."""
import task_graph as tg


def _tasks():
    return [
        {"id": "a", "description": "first", "depends_on": []},
        {"id": "b", "description": "second", "depends_on": ["a"]},
        {"id": "c", "description": "third", "depends_on": ["a", "b"]},
    ]


def test_init_and_ready_respects_dependencies(tmp_path):
    gf = tmp_path / "graph.json"
    tg.init(_tasks(), graph_file=gf)

    ready = {t["id"] for t in tg.get_ready(graph_file=gf)}
    assert ready == {"a"}  # only the dependency-free task is ready


def test_completing_tasks_unlocks_dependents(tmp_path):
    gf = tmp_path / "graph.json"
    tg.init(_tasks(), graph_file=gf)

    tg.mark_done("a", "ok", graph_file=gf)
    ready = {t["id"] for t in tg.get_ready(graph_file=gf)}
    assert ready == {"b"}  # c still waits on b

    tg.mark_done("b", "ok", graph_file=gf)
    ready = {t["id"] for t in tg.get_ready(graph_file=gf)}
    assert ready == {"c"}


def test_failed_task_does_not_unlock_dependents(tmp_path):
    gf = tmp_path / "graph.json"
    tg.init(_tasks(), graph_file=gf)
    tg.mark_failed("a", "boom", graph_file=gf)
    assert tg.get_ready(graph_file=gf) == []  # b/c never become ready


def test_status_report_lists_all_tasks(tmp_path):
    gf = tmp_path / "graph.json"
    tg.init(_tasks(), graph_file=gf)
    report = tg.status_report(graph_file=gf)
    assert "a" in report and "b" in report and "c" in report
