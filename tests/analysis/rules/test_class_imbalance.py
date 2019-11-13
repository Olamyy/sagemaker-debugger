# Standard Library
import uuid

# Third Party
import numpy as np
from tests.analysis.utils import generate_data

# First Party
from smdebug.exceptions import RuleEvaluationConditionMet
from smdebug.rules.generic import ClassImbalance
from smdebug.rules.rule_invoker import invoke_rule
from smdebug.trials import create_trial


def dump_data(values):
    run_id = str(uuid.uuid4())
    base_path = "ts_output/rule_invoker/"
    num_tensors = 1
    shape = 1000
    generate_data(
        path=base_path,
        trial=run_id,
        num_tensors=num_tensors,
        step=3,
        tname_prefix="labels",
        worker="algo-1",
        shape=shape,
        data=values,
        export_colls=True,
    )

    return base_path + run_id


def test_default():
    data = np.zeros(1000)
    data[-10:] = 1
    path = dump_data(data)
    tr = create_trial(path)
    rule = ClassImbalance(tr, labels_regex="labels_0", predictions_regex="labels_0")
    try:
        invoke_rule(rule, start_step=0, raise_eval_cond=True)
        assert False
    except RuleEvaluationConditionMet as e:
        print(e)
        assert e.step == 3