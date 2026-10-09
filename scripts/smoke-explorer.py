"""Actual browser interactions, no simulated research data."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import json, os
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'output'/'journal-explorer'
OUT.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('EXPLORER_TEST_URL','http://127.0.0.1:8768')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/explorer/?journal=30020',wait_until='networkidle')
    expect(page.locator('h1')).to_have_text('Journal of Organizational Behavior')
    assert page.locator('.heatmap tbody tr').count()>5
    page.screenshot(path=str(OUT/'desktop.png'),full_page=True)
    page.locator('[data-horizon="24"]').click()
    expect(page.locator('#outlook-content')).to_contain_text('24-month planning window')
    page.locator('#opportunities [data-call="illness"]').click()
    expect(page.locator('#plan-target')).to_have_value('2027-06-30')
    expect(page.locator('#plan-route')).to_have_value('empirical')
    page.locator('#plan-notes').fill('Test plan: verify recruitment access before committing.')
    page.locator('[data-done="0"]').check()
    with page.expect_download() as dl:page.locator('#export-plan').click()
    path=OUT/'exported-plan.md';dl.value.save_as(path)
    text=path.read_text(encoding='utf8');assert '2027-06-30' in text and 'Chronic-Illness' in text and 'Test plan:' in text
    with page.expect_download() as dl:page.locator('#export-calendar').click()
    cal=OUT/'exported-calendar.ics';dl.value.save_as(cal);assert 'BEGIN:VEVENT' in cal.read_text(encoding='utf8')
    page.reload(wait_until='networkidle')
    expect(page.locator('#plan-notes')).to_have_value('Test plan: verify recruitment access before committing.')
    expect(page.locator('[data-done="0"]')).to_be_checked()
    page.locator('#plan-target').fill('2026-01-01');page.locator('#plan-target').dispatch_event('change')
    expect(page.locator('#schedule-output')).to_contain_text('target date has already passed')
    page.locator('#opportunities [data-call="arcdi"]').click()
    expect(page.locator('#plan-route')).to_have_value('proposal')
    expect(page.locator('#schedule-output')).to_contain_text('no acceptance date is inferred')
    page.locator('.heatmap [data-topic="leadership"]').first.click()
    expect(page.locator('#topic-detail')).to_contain_text('Leadership')
    page.locator('#paper-search').fill('70132')
    expect(page.locator('#papers-list')).to_contain_text('10.1002/job.70132')
    # Failed live refresh retains verified saved evidence.
    page.route('https://api.crossref.org/**',lambda route:route.abort())
    page.locator('#refresh-crossref').click()
    expect(page.locator('#refresh-status')).to_contain_text('saved evidence retained',timeout=35000)
    page.locator('#journal-search').fill('Journal of Business Research')
    alt=page.locator('#journal-list option').filter(has_text='Journal of Business Research').evaluate_all("rows => rows.find(r=>r.textContent==='Journal of Business Research').value")
    page.locator('#journal-list').select_option(alt)
    expect(page.locator('h1')).to_have_text('Journal of Business Research')
    expect(page.locator('#calls-content')).to_contain_text('not yet been verified')
    expect(page.locator('#plan-notes')).to_have_value('')
    page.locator('#journal-search').fill('zzzz-no-journal')
    assert page.locator('#journal-list option').count()==0
    page.goto(BASE+'/explorer/?journal=30020',wait_until='networkidle')
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile horizontal overflow'
    page.screenshot(path=str(OUT/'mobile.png'),full_page=True)
    page.goto(BASE+'/?mode=publish',wait_until='domcontentloaded')
    expect(page.locator('#publishArea')).to_be_visible()
    expect(page.locator('#publishArea a[href="explorer/"]')).to_be_visible()
    assert not errors,errors
    browser.close()
print(json.dumps({'status':'PASS','desktop':1440,'mobile':390,'pageErrors':errors,'screenshots':str(OUT)}))
