import os

from stdl import st
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


def test_wrapped():
    text = "This is a long sentence that needs to be wrapped."
    assert st.wrapped(text, width=20) == "This is a long\nsentence that needs\nto be wrapped."
    assert (
        st.wrapped(text, width=20, newline="\r\n")
        == "This is a long\r\nsentence that needs\r\nto be wrapped."
    )
    assert st.wrapped("Short text", width=20) == "Short text"
    assert st.wrapped("", width=20) == ""


def test_len_without_ansi():
    no_ansi_text = "Normal text"
    assert st.ansi_len(no_ansi_text) == len(no_ansi_text)
    assert st.ansi_len(colored("TEXT", color="red")) == 4
    assert st.ansi_len(colored("TEXT", color="red", style="bold")) == 4
    assert st.ansi_len("") == 0


def test_ansi_ljust():
    no_ansi_text = "Normal"
    assert ansi_ljust(no_ansi_text, 10) == "Normal    "
    assert len(ansi_ljust(no_ansi_text, 10)) == 10

    red_text = colored("Red", color="red")
    ljust_red = ansi_ljust(red_text, 10)
    assert ansi_len(ljust_red) == 10
    assert ljust_red.startswith(red_text)

    bold_red_text = colored("Bold red", color="red", style="bold")
    ljust_bold_red = ansi_ljust(bold_red_text, 15, fillchar="-")
    assert ansi_len(ljust_bold_red) == 15
    assert ljust_bold_red.startswith(bold_red_text)

    assert ansi_ljust("", 5) == "     "


def test_ansi_rjust():
    no_ansi_text = "Normal"
    assert ansi_rjust(no_ansi_text, 10) == "    Normal"
    assert len(ansi_rjust(no_ansi_text, 10)) == 10

    red_text = colored("Red", color="red")
    rjust_red = ansi_rjust(red_text, 10)
    assert ansi_len(rjust_red) == 10
    assert rjust_red.endswith(red_text)

    bold_red_text = colored("Bold red", color="red", style="bold")
    rjust_bold_red = ansi_rjust(bold_red_text, 15, fillchar="-")
    assert ansi_len(rjust_bold_red) == 15
    assert rjust_bold_red.endswith(bold_red_text)

    assert ansi_rjust("", 5) == "     "


class TestStringFilter:
    def test_filename(self):
        assert st.sf.filename("file|name?.txt") == "filename.txt"
        assert st.sf.filename("file:name*.txt", replace_with="_") == "file_name_.txt"
        assert st.sf.filename("normal_filename.txt") == "normal_filename.txt"
        assert st.sf.filename("") == ""

    def test_filepath(self):
        assert st.sf.filepath(os.path.join("path", "to", "file|name?.txt")) == os.path.join(
            "path", "to", "filename.txt"
        )

        assert st.sf.filepath(
            os.path.join("path", "to", "file:name*.txt"), replace_with="_"
        ) == os.path.join("path", "to", "file_name_.txt")

        assert st.sf.filepath(os.path.join("normal", "path", "filename.txt")) == os.path.join(
            "normal", "path", "filename.txt"
        )

        assert st.sf.filepath("") == ""

    def test_ascii(self):
        assert st.sf.ascii("Héllö Wörld") == "Hll Wrld"
        assert st.sf.ascii("Héllö Wörld", replace_with="_") == "H_ll_ W_rld"
        assert st.sf.ascii("Hello World") == "Hello World"
        assert st.sf.ascii("") == ""
