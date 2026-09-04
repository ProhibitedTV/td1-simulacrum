import pytest

from td1_simulacrum import (
    TernaryWord,
    glyph_id_to_triad,
    glyph_ids_to_word,
    triad_to_glyph_id,
    word_to_glyph_ids,
)


def test_all_27_microglyph_states_round_trip() -> None:
    for glyph_id in range(27):
        triad = glyph_id_to_triad(glyph_id)
        assert triad_to_glyph_id(triad) == glyph_id


def test_12_trit_word_maps_to_four_reversible_microglyphs() -> None:
    word = TernaryWord.parse("+0--+000-++0")
    glyph_ids = word_to_glyph_ids(word)
    assert len(glyph_ids) == 4
    assert glyph_ids_to_word(glyph_ids) == word


def test_glyph_validation() -> None:
    with pytest.raises(ValueError):
        glyph_id_to_triad(27)
    with pytest.raises(ValueError):
        triad_to_glyph_id((0, 1))
    with pytest.raises(ValueError):
        word_to_glyph_ids(TernaryWord.parse("+0"))
