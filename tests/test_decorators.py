import json
import time

import pytest

from stdl.decorators import retry, timer


class TestTimer:
    def test_basic(self):
        @timer()
        def func():
            return 42

        assert func() == 42

    def test_with_arguments(self):
        @timer(show_args=True)
        def func(x, y):
            return x + y

        assert func(10, 20) == 30

    def test_method(self):
        class MyClass:
            @timer(serialize=True)
            def method(self):
                return "instance method"

        assert MyClass().method() == "instance method"

    def test_sink(self):
        sink = []

        @timer(sink=sink.append)
        def func():
            return 42

        assert func() == 42
        assert sink[0].startswith("'func' took")

    def test_sink_serialized(self):
        messages = []

        @timer(sink=messages.append, serialize=True)
        def func():
            return 42

        assert func() == 42
        message_dict = json.loads(messages[0])
        assert message_dict["name"] == "func"
        assert message_dict["time"] >= 0

    def test_show_args(self):
        sink = []

        @timer(show_args=True, sink=sink.append, serialize=True)
        def func(x, y):
            return x * y

        assert func(5, 4) == 20
        message_dict = json.loads(sink[0])
        assert message_dict["name"] == "func"
        assert message_dict["time"] >= 0
        assert message_dict["args"] == [5, 4]
        assert message_dict["kwargs"] == {}


class TestRetryDecorator:
    def test_retry_success(self):
        counter = [0]

        @retry(attempts=3)
        def successful_func():
            counter[0] += 1
            return "Success"

        assert successful_func() == "Success"
        assert counter[0] == 1

    def test_retry_failure(self):
        counter = [0]

        @retry(attempts=3)
        def failing_func():
            counter[0] += 1
            raise Exception("Failure")

        with pytest.raises(Exception) as excinfo:
            failing_func()
        assert str(excinfo.value) == "Failure"
        assert counter[0] == 3

    def test_retry_with_success_on_second_attempt(self):
        counter = [0]

        @retry(attempts=3)
        def func_with_success_on_second():
            counter[0] += 1
            if counter[0] < 2:
                raise Exception("Failure")
            return "Success"

        assert func_with_success_on_second() == "Success"
        assert counter[0] == 2
