from stdl.st import *


def test_snake_case():
    assert snake_case("FooBar") == "foo_bar"
    assert snake_case("Foo-Bar") == "foo_bar"
    assert snake_case("fooBar") == "foo_bar"
    assert snake_case("FOO BAR") == "foo_bar"
    assert snake_case("_fooBar") == "_foo_bar"


def test_kebab_case():
    assert kebab_case("foo_bar") == "foo-bar"
    assert kebab_case("foo____bar") == "foo-bar"
    assert kebab_case("foo bar") == "foo-bar"
    assert kebab_case("foo   bar") == "foo-bar"


def test_camel_case():
    assert camel_case("foo_bar") == "fooBar"
    assert camel_case("foo-bar") == "fooBar"
    assert camel_case("foo______BAR") == "fooBar"
    assert camel_case("foo______   BAR") == "fooBar"
    assert camel_case("foo _ _ BAR") == "fooBar"


def test_keep():
    assert keep("hello world", "hl") == "hlll"
    assert keep("hello world", "hl", "-") == "h-ll-----l-"
    assert keep("hello world", {"h", "l"}) == "hlll"
    assert keep("hello world", "heloword ") == "hello world"
    assert keep("", "") == ""


def test_remove():
    assert remove("hello world", "hl") == "eo word"
    assert remove("hello world", "hl", "-") == "-e--o wor-d"
    assert remove("hello world", {"h", "l"}) == "eo word"
    assert remove("hello world", "heloword ") == ""
    assert remove("hello world", "") == "hello world"
    assert remove("", "") == ""
