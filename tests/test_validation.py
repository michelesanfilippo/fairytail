import unittest
from lib import validate_workflow_args, validate_model_tier


class TestValidateWorkflowArgs(unittest.TestCase):
    def test_valid_task(self):
        self.assertTrue(validate_workflow_args({"task": "build a java service"}))

    def test_task_with_whitespace(self):
        self.assertTrue(validate_workflow_args({"task": "  write code  "}))

    def test_null_args_raises(self):
        with self.assertRaises((ValueError, TypeError)):
            validate_workflow_args(None)

    def test_string_args_raises(self):
        with self.assertRaises((ValueError, TypeError, AttributeError)):
            validate_workflow_args("string")

    def test_missing_task_raises(self):
        with self.assertRaises((ValueError, KeyError)):
            validate_workflow_args({})

    def test_empty_task_raises(self):
        with self.assertRaises(ValueError):
            validate_workflow_args({"task": ""})

    def test_whitespace_only_raises(self):
        with self.assertRaises(ValueError):
            validate_workflow_args({"task": "   "})

    def test_none_task_raises(self):
        with self.assertRaises((ValueError, TypeError)):
            validate_workflow_args({"task": None})

    def test_numeric_task_raises(self):
        with self.assertRaises((ValueError, TypeError)):
            validate_workflow_args({"task": 42})


class TestValidateModelTier(unittest.TestCase):
    # leader
    def test_fable_valid_leader(self):
        self.assertTrue(validate_model_tier("leader", "fable"))

    def test_opus_valid_leader(self):
        self.assertTrue(validate_model_tier("leader", "opus"))

    def test_sonnet_valid_leader(self):
        self.assertTrue(validate_model_tier("leader", "sonnet"))

    def test_haiku_invalid_leader(self):
        self.assertFalse(validate_model_tier("leader", "haiku"))

    def test_unknown_invalid(self):
        self.assertFalse(validate_model_tier("leader", "gpt4"))

    # workers
    def test_sonnet_valid_worker(self):
        self.assertTrue(validate_model_tier("workers", "sonnet"))

    def test_haiku_valid_worker(self):
        self.assertTrue(validate_model_tier("workers", "haiku"))

    def test_opus_valid_worker(self):
        self.assertTrue(validate_model_tier("workers", "opus"))

    def test_fable_valid_worker(self):
        self.assertTrue(validate_model_tier("workers", "fable"))

    # summary
    def test_haiku_valid_summary(self):
        self.assertTrue(validate_model_tier("summary", "haiku"))

    def test_sonnet_valid_summary(self):
        self.assertTrue(validate_model_tier("summary", "sonnet"))

    def test_fable_invalid_summary(self):
        self.assertFalse(validate_model_tier("summary", "fable"))

    def test_opus_invalid_summary(self):
        self.assertFalse(validate_model_tier("summary", "opus"))


if __name__ == "__main__":
    unittest.main()
