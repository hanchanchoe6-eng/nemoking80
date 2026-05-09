from dictionary_ingestion.domain import PageText
from dictionary_ingestion.splitter import compile_headword_pattern, split_entries


def test_split_entries_detects_headwords_and_metadata():
    pages = [
        PageText(
            page=3,
            text="""
            apple: a fruit
            often red or green
            banana — a long yellow fruit
            curved and sweet
            """,
        )
    ]

    entries = split_entries(pages, source_title="Sample", language="en")

    assert [entry.headword for entry in entries] == ["apple", "banana"]
    assert entries[0].page == 3
    assert entries[0].source_title == "Sample"
    assert entries[0].language == "en"
    assert "often red" in entries[0].body
    assert "curved and sweet" in entries[1].body


def test_custom_headword_pattern_is_supported():
    pattern = compile_headword_pattern(r"^\[(?P<headword>[^\]]+)\]")
    pages = [PageText(page=1, text="[λόγος] word, speech\ncontinued definition")]

    entries = split_entries(
        pages,
        source_title="Greek Lexicon",
        language="grc",
        headword_pattern=pattern,
    )

    assert len(entries) == 1
    assert entries[0].headword == "λόγος"
    assert entries[0].page == 1
