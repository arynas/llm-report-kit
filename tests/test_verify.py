"""Unsupported-number check: source names with digits are labels; invented figures still fail."""
import json
from pathlib import Path

from pptx import Presentation

from llm_report_kit.report import build_report
from llm_report_kit.verify import check_pptx, expected_pages

ROOT = Path(__file__).resolve().parent.parent
SOURCE_URL = 'https://www.gdeltproject.org/'


def krakatau_inputs():
    return json.loads((ROOT / 'examples/krakatau/report-inputs.json').read_text(encoding='utf-8'))


def figure_issues(inputs, deck):
    issues = []
    check_pptx(deck, inputs, expected_pages(inputs, SOURCE_URL),
               lambda kind, artifact, page, message: issues.append((kind, page, message)))
    return [issue for issue in issues if issue[0] == 'figures']


def test_source_domain_with_a_digit_is_not_an_unsupported_figure(tmp_path):
    # "ott", 10-23 Sep 2026: slide 3 shows the source liputan6.com; before the fix this was flagged as "6".
    inputs = json.loads((ROOT / 'tests/fixtures/ott-report-inputs.json').read_text(encoding='utf-8'))
    assert 'liputan6.com' in {story['source'] for story in inputs['facts']['top_stories'][:3]}
    deck = tmp_path / 'report.pptx'
    build_report(inputs, deck, 'GDELT Project', SOURCE_URL)
    assert figure_issues(inputs, deck) == []


def test_an_invented_number_in_slide_text_is_still_rejected(tmp_path):
    inputs = krakatau_inputs()
    deck = tmp_path / 'report.pptx'
    build_report(inputs, deck, 'GDELT Project', SOURCE_URL)
    presentation = Presentation(deck)
    shape = next(shape for shape in presentation.slides[2].shapes if shape.has_text_frame)
    shape.text_frame.text += ' Kerugian mencapai 4321 miliar.'
    presentation.save(deck)
    issues = figure_issues(inputs, deck)
    assert ('figures', 3, 'Unsupported number in slide text: 4321') in issues
