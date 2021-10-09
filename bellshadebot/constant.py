class Label:
    INVALID = "invalid"
    CHANGE = "awaiting changes"
    REVIEW = "awaiting reviews"
    DESCRIPTIVE_NAME = "require descriptive names"
    REQUIRE_TEST = "require test"
    TYPE_HINT = "require type hint"
    MERGE_CONFLICT = "merge conflict"
    FAILED_TEST = "test fail"
    DOCUMENTATION = "documentation"
    ENHANCEMENT = "enhancement"


GRETTING_COMMENT = """\
    ini adalah bellshade bot @{login}"""

EMPTY_ISSUE_BOD = """\
    # close issue karena invalid
    @{user_login}, issue di close karena deskripsi tidak ada isi
    """

EMPTY_PR_BODY_COMMENT = """\
    # close pull request karena invalid
    @{user_login}, pull request di close karena deskripsi tidak ada isi
    silahkan baca pedoman kontribusi terlebih dahulu [disini]\
        (https://github.com/bellshade/Python/blob/main/CONTRIBUTING.md)
    """

CHECKBOX_NOT_TICKED_COMMENT = """\
    # close pull request karena invalid
    @{user_login}, pull request di karena tidak ada menandai checkbox
    silahkan baca pedoman kontribusi terlebih dahulu [disini]\
        (https://github.com/bellshade/Python/blob/main/CONTRIBUTING.md)
    """

INVALID_EXTENSION_COMMENT = """\
    # close pull request karena invalid
    @{user_login}, pull request di close karena tidak ada extension yang valid
    silahkan baca pedoman kontribusi terlebih dahulu [disini]\
        (https://github.com/bellshade/Python/blob/main/CONTRIBUTING.md)
    """

PR_REVIEW_BODY = """\
    <details>
    <summary><b><em>lihat link yang relevan dibawah ini :arrow_down:</em></b></summary>
    <br>
    <blockquote>

    ## :link: link yang relevan
    ### repository
    - [peraturan kontribusi]\
         (https://github.com/bellshade/Python/blob/main/CONTRIBUTING.md)
    - [``doctest``](https://docs.python.org/3/library/doctest.html)
    - [``unittest``](https://docs.python.org/3/library/unittest.html)
    - [``pytest``](https://docs.pytest.org/en/latest/getting-started.html)

    <blockquote>
    </details>
    """

PR_REVIEW_COMMENT = (
    PR_REVIEW_BODY
    + """\
___
{content}

___
### **format: `[file path]:[line number]: [message]`**
"""
)
