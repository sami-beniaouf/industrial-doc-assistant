from docassistant.ingest import clean_text, make_id, split_words


def words(n: int) -> str:
    return " ".join(f"w{i}" for i in range(n))


def test_short_text_is_a_single_chunk():
    text = words(120)
    assert split_words(text) == [text]


def test_chunks_have_the_expected_size_and_overlap():
    chunks = [chunk.split() for chunk in split_words(words(700))]
    assert [len(chunk) for chunk in chunks] == [300, 300, 200]
    for previous, following in zip(chunks, chunks[1:], strict=False):
        assert previous[-50:] == following[:50]


def test_chunks_cover_the_whole_text_without_gaps():
    for n in (301, 349, 350, 351, 549, 550, 551, 700, 1200):
        original = words(n).split()
        chunks = [chunk.split() for chunk in split_words(words(n))]
        rebuilt = chunks[0] + [word for chunk in chunks[1:] for word in chunk[50:]]
        assert rebuilt == original, n
        assert all(len(chunk) <= 300 for chunk in chunks), n


def test_make_id_is_stable_and_valid_for_search_keys():
    first = make_id("a.pdf", 3, 0)
    assert first == make_id("a.pdf", 3, 0)
    assert len(first) == 40
    assert set(first) <= set("0123456789abcdef")


def test_make_id_changes_with_source_page_or_position():
    ids = {make_id("a.pdf", 3, 0), make_id("b.pdf", 3, 0), make_id("a.pdf", 4, 0), make_id("a.pdf", 3, 1)}
    assert len(ids) == 4


def test_clean_text_rejoins_compound_words_split_at_line_end():
    assert clean_text("Machines- outils et électro- érosion") == "Machines-outils et électro-érosion"


def test_clean_text_cannot_tell_a_cut_word_from_a_compound():
    # Known limitation: without a dictionary the hyphen is kept ("auto-matique").
    assert clean_text("machine auto- matique") == "machine auto-matique"


def test_clean_text_keeps_spaced_dashes_and_collapses_whitespace():
    assert clean_text("EN ISO 16089 - Machines\n  à   meuler") == "EN ISO 16089 - Machines à meuler"
