# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 2623-4159

def http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 12) -> Dict:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

@st.cache_data(show_spinner=False, ttl=900)
def fetch_arbeitnow_jobs(query: str, location: str = "", limit: int = 15) -> List[Dict]:
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        payload = http_get_json(url)
    except Exception:
        return []

    items = payload.get("data", []) if isinstance(payload, dict) else []
    q = (query or "").casefold()
    loc = (location or "").casefold()
    if loc.startswith("anywhere in "):
        loc = ""
    results = []

    for item in items:
        title = str(item.get("title", "")).strip()
        company = str(item.get("company_name", "")).strip()
        job_location = str(item.get("location", "")).strip()
        description = str(item.get("description", "")).strip()
        tags = ", ".join(item.get("tags", [])[:5]) if isinstance(item.get("tags"), list) else ""
        remote = bool(item.get("remote", False))
        url_apply = item.get("url") or item.get("job_url") or ""

        haystack = " ".join([title, company, job_location, description, tags]).casefold()
        if q and q not in haystack:
            continue
        if loc and loc not in haystack and not remote:
            continue

        results.append({
            "source": "Arbeitnow",
            "title": title,
            "company": company,
            "location": job_location or ("Remote" if remote else "Germany"),
            "remote": remote,
            "url": url_apply,
            "summary": tags or (description[:220] + "..." if description else "")
        })
        if len(results) >= limit:
            break

    return results

@st.cache_data(show_spinner=False, ttl=900)
def fetch_arbeitsagentur_jobs(query: str, location: str = "", limit: int = 15) -> List[Dict]:
    client_id = (os.getenv("BA_JOBS_API_KEY") or get_streamlit_secret("BA_JOBS_API_KEY") or "c003a37f-024f-462a-b36d-b001be4cd24a")
    normalized_location = "" if str(location or "").lower().startswith("anywhere in ") else (location or "")
    params = {
        "was": query or "",
        "wo": normalized_location,
        "size": str(limit),
    }
    url = "https://jobsuche.api.bund.dev/pc/v4/app/jobs?" + urllib.parse.urlencode(params)

    try:
        payload = http_get_json(url, headers={"X-API-Key": client_id, "User-Agent": "Mozilla/5.0"}, timeout=12)
    except Exception:
        return []

    raw_items = []
    if isinstance(payload, dict):
        for key in ["stellenangebote", "jobOffers", "jobs", "data"]:
            value = payload.get(key)
            if isinstance(value, list):
                raw_items = value
                break

    results = []
    for item in raw_items:
        title = str(item.get("beruf") or item.get("titel") or item.get("title") or "").strip()
        employer = item.get("arbeitgeber") or item.get("company") or {}
        if isinstance(employer, dict):
            company = str(employer.get("name") or employer.get("firma") or "").strip()
        else:
            company = str(employer or "").strip()

        location_value = item.get("arbeitsort") or item.get("arbeitsorte") or item.get("location") or {}
        if isinstance(location_value, list) and location_value:
            first_loc = location_value[0]
            if isinstance(first_loc, dict):
                place = ", ".join([str(first_loc.get("ort") or "").strip(), str(first_loc.get("region") or "").strip()]).strip(", ")
            else:
                place = str(first_loc)
        elif isinstance(location_value, dict):
            place = ", ".join([str(location_value.get("ort") or "").strip(), str(location_value.get("region") or "").strip()]).strip(", ")
        else:
            place = str(location_value or "").strip()

        refnr = str(item.get("refnr") or item.get("referenznummer") or "").strip()
        detail_url = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{urllib.parse.quote(refnr)}" if refnr else "https://www.arbeitsagentur.de/jobsuche/"
        summary = str(item.get("eintrittsdatum") or item.get("aktuelleVeroeffentlichungsdatum") or item.get("modifikationsTimestamp") or "").strip()

        if title:
            results.append({
                "source": "Bundesagentur fur Arbeit",
                "title": title,
                "company": company or "Employer not shown",
                "location": place or (location or "Germany"),
                "remote": False,
                "url": detail_url,
                "summary": summary
            })
        if len(results) >= limit:
            break

    return results

def get_status_job_modifiers(user_status: str, country_name: str = "") -> List[str]:
    status = (user_status or "").lower()
    if is_student_thesis_status(user_status):
        return get_student_job_keywords(country_name)
    if any(x in status for x in ["fresh", "graduate", "absolvent", "entry level"]):
        return ["junior", "entry level", "trainee", "graduate", "internship", "no experience"]
    if any(x in status for x in ["career changer", "quereinsteiger", "changer"]):
        return ["junior", "career changer", "entry level", "trainee", "quereinsteiger"]
    if any(x in status for x in ["apply online", "remote", "online"]):
        return ["remote", "online", "work from home", "hybrid", "junior", "entry level"]
    if any(x in status for x in ["returning", "break", "pause"]):
        return ["returnship", "part time", "junior", "entry level", "back to work"]
    if any(x in status for x in ["experienced", "senior"]):
        return ["experienced", "specialist", "senior"]
    return ["junior", "entry level", "specialist"]

def build_live_job_queries(roles: List[str], user_status: str, max_queries: int = 18, country_name: str = "") -> List[str]:
    base_roles = [r.strip() for r in roles if r and r.strip()]
    if not base_roles:
        base_roles = ["Data Analyst", "IT Support", "Customer Support", "Business Analyst"]
    modifiers = get_status_job_modifiers(user_status, country_name)
    queries: List[str] = []
    for role in base_roles[:6]:
        if role not in queries:
            queries.append(role)
        for modifier in modifiers[:5]:
            candidate = f"{modifier} {role}"
            if candidate not in queries:
                queries.append(candidate)
        for modifier in ["remote", "online", "hybrid"]:
            candidate = f"{role} {modifier}"
            if candidate not in queries:
                queries.append(candidate)
        if len(queries) >= max_queries:
            break
    return queries[:max_queries]

def score_job_for_user(job: Dict, user_status: str, roles: List[str], country_name: str = "") -> int:
    text = " ".join([str(job.get(k, "")) for k in ["title", "summary", "company", "location", "source"]]).lower()
    score = 0
    for role in roles:
        role_words = [w for w in re.findall(r"[a-zA-Z]+", role.lower()) if len(w) > 2]
        score += sum(6 for w in role_words if w in text)
    for mod in get_status_job_modifiers(user_status, country_name):
        if mod.lower() in text:
            score += 12
    status = (user_status or "").lower()
    if any(x in status for x in ["fresh", "graduate", "student", "career changer", "returning"]):
        if any(x in text for x in ["senior", "lead", "principal", "manager"]):
            score -= 20
        if any(x in text for x in ["junior", "entry", "trainee", "intern", "working student", "graduate"]):
            score += 20
    if job.get("remote"):
        score += 5
    return score

def sort_jobs_for_user(jobs: List[Dict], user_status: str, roles: List[str], country_name: str = "") -> List[Dict]:
    return sorted(jobs, key=lambda job: score_job_for_user(job, user_status, roles, country_name), reverse=True)

def fetch_live_jobs_for_germany(roles: List[str], location: str = "", user_status: str = "") -> List[Dict]:
    results: List[Dict] = []
    search_queries = build_live_job_queries(roles, user_status, max_queries=8, country_name="Germany")

    # German job boards often use German role keywords. Add broad local-language fallbacks
    # so live search does not return only 0-3 results for English role titles.
    german_fallback_queries = [
        "Junior", "Quereinsteiger", "Berufseinsteiger", "Trainee", "Praktikum",
        "Werkstudent", "Abschlussarbeit", "Bachelorarbeit", "Masterarbeit", "Thesis",
        "Datenanalyst", "Data Analyst", "Business Analyst", "IT Support",
        "IT Support Mitarbeiter", "Helpdesk", "Kundenservice", "Customer Support",
        "Sachbearbeiter", "Backoffice", "Service Desk"
    ]
    for q in german_fallback_queries:
        if q not in search_queries:
            search_queries.append(q)

    for query in search_queries[:12]:
        results.extend(fetch_arbeitsagentur_jobs(query, location, limit=10))
        results.extend(fetch_arbeitnow_jobs(query, location, limit=10))

    # If a city search is too narrow, broaden once to the whole country.
    if len(results) < 12 and location and location.lower() not in {"germany", "anywhere in germany"}:
        for query in search_queries[:18]:
            results.extend(fetch_arbeitsagentur_jobs(query, "", limit=25))
            results.extend(fetch_arbeitnow_jobs(query, "", limit=25))

    deduped = []
    seen = set()
    for item in results:
        key = (item.get("source", "") + "|" + item.get("title", "") + "|" + item.get("company", "") + "|" + item.get("location", "")).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return sort_jobs_for_user(deduped, user_status, roles, "Germany")[:35]


def render_live_jobs(jobs: List[Dict], country_name: str = "", max_visible: int = 30, roles: Optional[List[str]] = None, cv_text: str = ""):
    """Render live jobs without making users feel there are '0 jobs in a country'.

    Important UX change:
    - If strong profile matches are not found, show the best available broader live jobs instead of a hard zero.
    - If live APIs return nothing, clearly explain that live sources are limited and guide users to platform links.
    """
    roles = roles or []
    country_lower = (country_name or "").strip().lower()
    adzuna_ready = bool(os.getenv("ADZUNA_APP_ID") or get_streamlit_secret("ADZUNA_APP_ID")) and bool(os.getenv("ADZUNA_APP_KEY") or get_streamlit_secret("ADZUNA_APP_KEY"))

    original_jobs = list(jobs or [])
    filtered_jobs = [job for job in original_jobs if job_location_relevant(job, country_name)]

    # Do not throw away all jobs just because a source gives a weak/empty location.
    # This was the main reason users saw "0 jobs in Germany", which feels unbelievable.
    if country_name and filtered_jobs:
        jobs = filtered_jobs
    elif country_lower == "germany" and original_jobs:
        jobs = original_jobs
    else:
        jobs = filtered_jobs if country_name else original_jobs

    title = f"Live job openings in {country_name}" if country_name else "Live job openings"
    st.markdown(f"### {title}")
    st.caption("WorkZo ranks live results by profile fit. If strong matches are limited, broader jobs are shown so users can still continue the journey.")

    if not jobs:
        with st.container():
            st.markdown("""
<div class='card' style='border-color:rgba(96,165,250,0.32); background:rgba(37,99,235,0.14);'>
  <div class='section-title'>Live sources did not return jobs for this exact search</div>
  <div class='small-muted' style='color:#cbd5e1;'>This does not mean there are no jobs. It usually means the free live-source/API coverage is limited or the search is too narrow.</div>
  <ul style='margin-top:10px; color:#e2e8f0;'>
    <li><b>Broaden the role:</b> try IT Support, Data Analyst, Customer Support, Service Desk.</li>
    <li><b>Broaden the location:</b> search the whole country first.</li>
    <li><b>Next step:</b> open platform links below, copy one job description, then use Understand Job.</li>
  </ul>
</div>
""", unsafe_allow_html=True)
        if not adzuna_ready and country_lower != "germany":
            st.caption("Tip for founder: add ADZUNA_APP_ID and ADZUNA_APP_KEY in Streamlit secrets to improve global live-job coverage.")
        return

    ranked_jobs = []
    for job in jobs:
        score, reasons = estimate_job_match_score(job, roles, cv_text)
        job = dict(job)
        job["_match_score"] = score
        job["_match_reasons"] = reasons
        ranked_jobs.append(job)

    ranked_jobs.sort(key=lambda x: x.get("_match_score", 0), reverse=True)

    strong_jobs = [job for job in ranked_jobs if job.get("_match_score", 0) >= 70]
    possible_jobs = [job for job in ranked_jobs if 45 <= job.get("_match_score", 0) < 70]
    weak_jobs = [job for job in ranked_jobs if job.get("_match_score", 0) < 45]

    visible_jobs = (strong_jobs + possible_jobs)[:max_visible]
    showing_broader_results = False
    if not visible_jobs and ranked_jobs:
        # Instead of showing "0", show the best available lower-fit jobs with a clear warning.
        visible_jobs = ranked_jobs[:min(max_visible, 8)]
        showing_broader_results = True

    if showing_broader_results:
        st.warning("No strong profile matches were found, so WorkZo is showing broader live results. Use them as search leads, then paste a job description into Understand Job.")
    else:
        st.caption(f"Showing {len(visible_jobs)} relevant/broader openings. Hidden weak matches: {len(weak_jobs)}.")

    def render_clickable_job_card(job: Dict, compact: bool = False):
        summary = (job.get("summary", "") or "—")
        limit = 130 if compact else 190
        if len(summary) > limit:
            summary = summary[:limit].rsplit(" ", 1)[0] + "..."
        url = job.get("url") or "#"
        title_html = html.escape(str(job.get("title", "Role")))
        company_html = html.escape(str(job.get("company", "Employer not shown")))
        location = str(job.get("location", "") or "Location not shown")
        source = str(job.get("source", "") or "Job source")
        meta_html = html.escape(f"{location} • {source}")
        summary_html = html.escape(summary)
        match_score = int(job.get("_match_score", 0) or 0)
        reasons = job.get("_match_reasons", []) or []
        reason_html = "".join([f"<span class='pill'>✓ {html.escape(str(r))}</span>" for r in reasons[:3]])
        badge_label = f"{match_score}% fit" if match_score >= 45 else f"{match_score}% broad"
        job_html = f"""
<a href="{html.escape(url, quote=True)}" target="_blank" style="text-decoration:none; color:inherit;">
  <div class="card" style="cursor:pointer; transition:0.15s; border-color:rgba(96,165,250,0.32);">
    <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
      <div>
        <div class="section-title">{title_html}</div>
        <div><strong>{company_html}</strong></div>
        <div class="small-muted">{meta_html}</div>
      </div>
      <div class="beta-badge">{badge_label}</div>
    </div>
    <div style="margin-top:8px; color:#cbd5e1;">{summary_html}</div>
    <div style="margin-top:10px;">{reason_html}</div>
    <div style="margin-top:10px; font-size:0.9rem; color:#93c5fd;">↗ Open job</div>
  </div>
</a>
"""
        st.markdown(job_html, unsafe_allow_html=True)

    top_jobs = visible_jobs[:5]
    remaining_jobs = visible_jobs[5:]
    for job in top_jobs:
        render_clickable_job_card(job)

    if remaining_jobs:
        with st.expander(f"Show {len(remaining_jobs)} more live results", expanded=False):
            for job in remaining_jobs:
                render_clickable_job_card(job, compact=True)

def country_to_indeed_domain(country_name: str) -> str:
    country = (country_name or "").strip().lower()
    domain_map = {
        "germany": "de.indeed.com", "netherlands": "nl.indeed.com", "the netherlands": "nl.indeed.com",
        "united kingdom": "uk.indeed.com", "uk": "uk.indeed.com", "ireland": "ie.indeed.com",
        "united states": "www.indeed.com", "usa": "www.indeed.com", "canada": "ca.indeed.com",
        "india": "in.indeed.com", "australia": "au.indeed.com", "new zealand": "nz.indeed.com",
        "france": "fr.indeed.com", "spain": "es.indeed.com", "italy": "it.indeed.com",
        "austria": "at.indeed.com", "switzerland": "ch.indeed.com", "belgium": "be.indeed.com",
        "sweden": "se.indeed.com", "denmark": "dk.indeed.com", "norway": "no.indeed.com",
        "finland": "fi.indeed.com", "poland": "pl.indeed.com", "singapore": "sg.indeed.com",
        "south africa": "za.indeed.com", "brazil": "br.indeed.com", "mexico": "mx.indeed.com",
        "japan": "jp.indeed.com", "united arab emirates": "ae.indeed.com"
    }
    return domain_map.get(country, "www.indeed.com")


def get_country_linkedin_geo(country_name: str) -> str:
    # LinkedIn works globally without geoId; country name in location is enough for broad matching.
    return urllib.parse.quote(country_name or "")


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_remotive_jobs(query: str, location: str = "", limit: int = 20) -> List[Dict]:
    """Free remote-job API fallback. Useful for global/online job seekers."""
    q = (query or "").strip()
    if not q:
        return []
    url = "https://remotive.com/api/remote-jobs?" + urllib.parse.urlencode({"search": q, "limit": str(limit)})
    try:
        payload = http_get_json(url, timeout=12)
    except Exception:
        return []
    items = payload.get("jobs", []) if isinstance(payload, dict) else []
    results: List[Dict] = []
    for item in items[:limit]:
        title = str(item.get("title", "")).strip()
        company = str(item.get("company_name", "")).strip()
        url_apply = str(item.get("url", "")).strip()
        category = str(item.get("category", "")).strip()
        candidate_required_location = str(item.get("candidate_required_location", "Remote")).strip()
        description = re.sub(r"<[^>]+>", " ", str(item.get("description", "")))
        description = re.sub(r"\s+", " ", description).strip()
        if title:
            results.append({
                "source": "Remotive",
                "title": title,
                "company": company or "Employer not shown",
                "location": candidate_required_location or "Remote / Worldwide",
                "remote": True,
                "url": url_apply,
                "summary": category or (description[:220] + "..." if description else "Remote role")
            })
    return results


def get_global_job_search_query(role: str, country_name: str, location: str, user_status: str = "") -> str:
    role = (role or "jobs").strip()
    loc = (location or country_name or "").strip()
    status = (user_status or "").lower()
    modifiers = []
    if is_student_thesis_status(user_status):
        modifiers.extend(get_student_job_keywords(country_name)[:3])
    elif any(x in status for x in ["fresh", "graduate"]):
        modifiers.extend(["entry level", "junior", "graduate"])
    elif any(x in status for x in ["career changer", "quereinsteiger"]):
        modifiers.extend(["career changer", "junior"])
    elif any(x in status for x in ["online", "remote"]):
        modifiers.extend(["remote", "online"])
    elif any(x in status for x in ["experienced", "senior"]):
        modifiers.extend(["experienced"])
    prefix = " ".join(modifiers[:2])
    return " ".join([prefix, role, "jobs", loc]).strip()

def get_job_board_links(country_name: str, location: str, role: str = "", user_status: str = "") -> List[Tuple[str, str]]:

    country_name = (country_name or "").strip()
    location = (location or country_name or "").strip()
    role = (role or "jobs").strip()
    country = country_name.lower()
    q_text = get_global_job_search_query(role, country_name, location, user_status)
    q = urllib.parse.quote(q_text)
    loc_q = urllib.parse.quote(location or country_name)
    role_q = urllib.parse.quote(role)
    indeed_domain = country_to_indeed_domain(country_name)

    boards: List[Tuple[str, str]] = [
        ("LinkedIn Jobs", f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc_q}"),
        ("Indeed", f"https://{indeed_domain}/jobs?q={q}&l={loc_q}"),
        ("Google Jobs", f"https://www.google.com/search?q={q}"),
    ]

    if country == "germany":
        boards.extend([
            ("StepStone Germany", f"https://www.stepstone.de/jobs/{role_q}/in-{loc_q}"),
            ("XING Jobs", f"https://www.xing.com/jobs/search?keywords={role_q}&location={loc_q}"),
            ("Bundesagentur fur Arbeit", f"https://www.arbeitsagentur.de/jobsuche/suche?was={role_q}&wo={loc_q}"),
        ])
    elif country in {"netherlands", "the netherlands"}:
        boards.extend([
            ("National Vacaturebank", f"https://www.nationalevacaturebank.nl/vacatures/zoekterm/{role_q}"),
            ("Werk.nl", f"https://www.werk.nl/werkzoekenden/vacatures/?q={role_q}"),
            ("Iamexpat Jobs", f"https://www.iamexpat.nl/career/jobs-netherlands?search={role_q}"),
        ])
    elif country in {"united kingdom", "uk"}:
        boards.extend([
            ("Reed", f"https://www.reed.co.uk/jobs/{role_q}-jobs-in-{loc_q}"),
            ("Totaljobs", f"https://www.totaljobs.com/jobs/{role_q}/in-{loc_q}"),
            ("CV-Library", f"https://www.cv-library.co.uk/{role_q}-jobs-in-{loc_q}"),
        ])
    elif country in {"united states", "usa"}:
        boards.extend([
            ("USAJobs", f"https://www.usajobs.gov/Search/Results?k={role_q}&l={loc_q}"),
            ("Dice Tech Jobs", f"https://www.dice.com/jobs?q={role_q}&location={loc_q}"),
            ("ZipRecruiter", f"https://www.ziprecruiter.com/jobs-search?search={role_q}&location={loc_q}"),
        ])
    elif country == "india":
        boards.extend([
            ("Naukri", f"https://www.naukri.com/{role_q}-jobs-in-{loc_q}"),
            ("Foundit", f"https://www.foundit.in/search/{role_q}-jobs-in-{loc_q}"),
            ("TimesJobs", f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&txtKeywords={role_q}&txtLocation={loc_q}"),
        ])
    elif country == "canada":
        boards.extend([
            ("Job Bank Canada", f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={role_q}&locationstring={loc_q}"),
            ("Workopolis", f"https://www.workopolis.com/jobsearch/{role_q}-jobs/{loc_q}"),
        ])
    elif country == "australia":
        boards.extend([
            ("Seek Australia", f"https://www.seek.com.au/{role_q}-jobs/in-{loc_q}"),
            ("Jora Australia", f"https://au.jora.com/{role_q}-jobs-in-{loc_q}"),
        ])
    else:
        boards.extend([
            ("Glassdoor", f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={role_q}&locT=N&locId=&locKeyword={loc_q}"),
            ("Remote OK", f"https://remoteok.com/remote-{role_q}-jobs"),
            ("Remotive", f"https://remotive.com/remote-jobs/search?search={role_q}"),
        ])

    # Always include remote/global sources because some users apply internationally.
    boards.extend([
        ("Remotive Remote Jobs", f"https://remotive.com/remote-jobs/search?search={role_q}"),
        ("Remote OK", f"https://remoteok.com/remote-{role_q}-jobs"),
    ])

    deduped = []
    seen = set()
    for label, url in boards:
        key = (label + url).lower()
        if key not in seen:
            seen.add(key)
            deduped.append((label, url))
    return deduped

def render_job_board_search_cards(country_name: str, location: str, roles: List[str], user_status: str = ""):
    st.markdown("### Continue searching on job platforms")
    st.caption("Open broader searches, then paste one promising job description into Understand Job to check your fit.")
    for role in roles[:3]:
        with st.expander(f"{role} — search links", expanded=False):
            links = get_job_board_links(country_name, location, role, user_status)[:5]
            compact_links = []
            for label, url in links:
                safe_label = html.escape(label)
                safe_url = html.escape(url, quote=True)
                compact_links.append(
                    f'<a class="compact-job-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">↗ {safe_label}</a>'
                )
            st.markdown(
                "<div class='compact-job-link-grid'>" + "".join(compact_links) + "</div>",
                unsafe_allow_html=True
            )


def job_location_relevant(job: Dict, country_name: str) -> bool:
    """Return True when a live job result is relevant for the selected country."""
    country = (country_name or "").strip().lower()
    if not country:
        return True

    loc = str(job.get("location", "") or "").lower()
    source = str(job.get("source", "") or "").lower()
    title = str(job.get("title", "") or "").lower()
    summary = str(job.get("summary", "") or "").lower()
    text = f"{title} {summary} {loc} {source}"

    # Germany-specific sources sometimes return empty/short location fields.
    # Trust local German sources unless the text clearly points to another country.
    if country == "germany" and ("arbeitsagentur" in source or "arbeitnow" in source):
        other_markers = ["united states", "usa", "india", "canada", "united kingdom", "uk", "australia", "france", "spain", "portugal", "netherlands"]
        if not any(marker in text for marker in other_markers):
            return True

    aliases = {
        "germany": ["germany", "deutschland", "berlin", "munich", "munchen", "hamburg", "frankfurt", "cologne", "koln", "stuttgart", "dusseldorf", "remote in germany"],
        "united states": ["united states", "usa", "u.s.", "remote in us", "remote in usa"],
        "usa": ["united states", "usa", "u.s.", "remote in us", "remote in usa"],
        "united kingdom": ["united kingdom", "uk", "england", "london", "remote in uk"],
        "uk": ["united kingdom", "uk", "england", "london", "remote in uk"],
        "india": ["india", "bangalore", "bengaluru", "chennai", "mumbai", "pune", "hyderabad", "delhi"],
        "canada": ["canada", "toronto", "vancouver", "montreal", "remote in canada"],
        "france": ["france", "paris", "remote in france"],
        "netherlands": ["netherlands", "amsterdam", "rotterdam", "remote in netherlands"],
        "the netherlands": ["netherlands", "amsterdam", "rotterdam", "remote in netherlands"],
        "australia": ["australia", "sydney", "melbourne", "remote in australia"],
        "portugal": ["portugal", "lisbon", "porto", "remote in portugal"],
        "spain": ["spain", "madrid", "barcelona", "remote in spain"],
        "italy": ["italy", "milan", "rome", "remote in italy"],
    }

    country_terms = aliases.get(country, [country])
    if any(term in text for term in country_terms):
        return True

    global_remote_terms = ["remote worldwide", "worldwide", "global remote", "remote - worldwide", "europe remote", "remote europe", "emea remote"]
    if any(term in text for term in global_remote_terms):
        return True

    other_country_markers = ["usa", "united states", "india", "canada", "united kingdom", "uk", "australia", "france", "spain", "portugal", "netherlands"]
    if "remote" in text and not any(term in text for term in country_terms):
        if any(marker in text for marker in other_country_markers if marker not in country_terms):
            return False

    return False


def estimate_job_match_score(job: Dict, roles: List[str], cv_text: str = "") -> Tuple[int, List[str]]:
    """Stricter profile-aware job matching.

    The score compares five areas instead of simple keyword counting:
    1) job-title fit, 2) skills/tools fit, 3) experience level,
    4) language requirements, and 5) location/work-mode fit.
    Jobs below 50% are hidden in render_live_jobs.
    """
    job_text = " ".join(str(job.get(k, "")) for k in ["title", "company", "summary", "category", "location", "source"]).lower()
    title_text = str(job.get("title", "") or "").lower()
    location_text = str(job.get("location", "") or "").lower()
    cv_lower = (cv_text or "").lower()
    reasons: List[str] = []

    def contains_any(text: str, terms: List[str]) -> bool:
        return any(term in text for term in terms)

    def token_set(text: str) -> set:
        stop = {"and", "the", "for", "with", "from", "your", "you", "are", "job", "role", "specialist", "engineer", "manager"}
        return {w for w in re.findall(r"[a-zA-Z][a-zA-Z+#.]{1,}", text.lower()) if w not in stop and len(w) > 2}

    # -------------------------
    # 1) Language requirement gate
    # -------------------------
    language_terms = {
        "Japanese": ["japanese", "japanisch"],
        "Spanish": ["spanish", "spanisch"],
        "French": ["french", "franzosisch", "franzoesisch"],
        "Portuguese": ["portuguese", "portugiesisch"],
        "Dutch": ["dutch", "niederlandisch", "niederlaendisch"],
        "German": ["german", "deutsch"],
        "English": ["english", "englisch"],
        "Italian": ["italian", "italienisch"],
        "Arabic": ["arabic", "arabisch"],
        "Hindi": ["hindi"],
        "Chinese": ["chinese", "mandarin", "chinesisch"],
    }
    missing_languages: List[str] = []
    matched_languages: List[str] = []
    for lang, terms in language_terms.items():
        hard_required = any(
            f"{t} speaking" in job_text or f"{t}-speaking" in job_text or
            f"fluent {t}" in job_text or f"native {t}" in job_text or
            f"{t} speaker" in job_text or f"language: {t}" in job_text or
            f"{t} required" in job_text or f"{t} mandatory" in job_text
            for t in terms
        )
        if hard_required:
            if any(t in cv_lower for t in terms):
                matched_languages.append(lang)
            else:
                missing_languages.append(lang)

    # -------------------------
    # 2) Job-title fit, with role families
    # -------------------------
    role_families = {
        "technical_support": ["technical support", "it support", "support engineer", "service desk", "helpdesk", "help desk", "application support", "support specialist", "customer support engineer"],
        "data": ["data analyst", "business intelligence", "bi analyst", "reporting analyst", "analytics", "tableau", "power bi", "sql analyst"],
        "customer_success": ["customer success", "customer support", "client support", "customer care", "account support", "implementation specialist"],
        "software": ["software engineer", "developer", "frontend", "backend", "full stack", "java developer", "python developer"],
        "sales_marketing": ["sales", "marketing", "seo", "content", "business development"],
    }

    cv_family_scores = {family: 0 for family in role_families}
    job_family_scores = {family: 0 for family in role_families}
    for family, terms in role_families.items():
        cv_family_scores[family] = sum(1 for t in terms if t in cv_lower)
        job_family_scores[family] = sum(1 for t in terms if t in job_text)

    selected_role_text = " ".join(roles or []).lower()
    selected_tokens = token_set(selected_role_text)
    title_tokens = token_set(title_text)
    title_overlap = len(selected_tokens & title_tokens) / max(1, len(selected_tokens)) if selected_tokens else 0

    title_score = 0
    if selected_role_text and any(role.lower().strip() and role.lower().strip() in title_text for role in roles[:6]):
        title_score = 30
        reasons.append("Strong job-title fit")
    elif title_overlap >= 0.65:
        title_score = 24
        reasons.append("Relevant job title")
    else:
        shared_family = [f for f in role_families if cv_family_scores[f] and job_family_scores[f]]
        if shared_family:
            title_score = 18
            family_label = shared_family[0].replace("_", " ").title()
            reasons.append(f"Same role family: {family_label}")
        elif title_overlap >= 0.35:
            title_score = 12
            reasons.append("Partial title fit")

    # -------------------------
    # 3) Skills and tools fit
    # -------------------------
    skill_terms = [
        "python", "sql", "excel", "tableau", "power bi", "pandas", "matplotlib", "seaborn", "gcp", "aws", "api", "rest api",
        "data analysis", "data visualization", "machine learning", "generative ai", "a/b testing", "dashboard", "reporting",
        "technical support", "it support", "customer support", "service desk", "helpdesk", "troubleshooting", "ticket", "tickets",
        "itsm", "itil", "manageengine", "servicedesk plus", "zoho", "crm", "saas", "windows", "linux", "network", "hardware", "software",
        "communication", "documentation", "knowledge base", "customer-facing", "stakeholder", "problem solving"
    ]
    cv_skills = {s for s in skill_terms if s in cv_lower}
    job_skills = {s for s in skill_terms if s in job_text}
    matched_skills = sorted(cv_skills & job_skills)
    skill_score = min(28, len(matched_skills) * 5)
    if matched_skills:
        reasons.append("Skills fit: " + ", ".join([s.title() for s in matched_skills[:3]]))

    # Boost transferable support/data combinations, but do not over-score unrelated titles.
    if any(t in cv_lower for t in ["technical support", "it support", "customer support", "servicedesk", "service desk"]) and any(t in job_text for t in ["technical support", "it support", "customer support", "service desk", "helpdesk"]):
        skill_score += 8
        if "Support background" not in reasons:
            reasons.append("Support background fits")
    if any(t in cv_lower for t in ["python", "sql", "tableau", "data analysis"]) and any(t in job_text for t in ["data analyst", "sql", "tableau", "power bi", "reporting", "analytics"]):
        skill_score += 6
        reasons.append("Data tools fit")
    skill_score = min(32, skill_score)

    # -------------------------
    # 4) Experience/seniority fit
    # -------------------------
    seniority_score = 12
    senior_terms = ["senior", "lead", "principal", "head of", "director", "team lead", "manager"]
    entry_terms = ["junior", "entry", "trainee", "graduate", "associate", "fresher", "1st level", "first level", "level 1"]
    mid_terms = ["specialist", "engineer", "analyst", "consultant", "2nd level", "second level"]

    if contains_any(job_text, senior_terms):
        seniority_score = 2
        reasons.append("Seniority may be too high")
    elif contains_any(job_text, entry_terms):
        seniority_score = 16
        reasons.append("Realistic seniority")
    elif contains_any(job_text, mid_terms):
        seniority_score = 13
        reasons.append("Mid-level fit possible")

    # -------------------------
    # 5) Location/work-mode fit
    # -------------------------
    location_score = 8
    if contains_any(job_text, ["remote", "hybrid", "home office", "work from home"]):
        location_score = 10
        reasons.append("Flexible work option")
    elif location_text:
        location_score = 7

    # Language fit score. Missing hard-required languages are a strong penalty and score cap.
    language_score = 8
    if matched_languages:
        language_score = 10
        reasons.append("Language fit: " + ", ".join(matched_languages[:2]))
    if missing_languages:
        language_score = 0
        reasons.append("Missing required language: " + ", ".join(missing_languages[:2]))

    raw_score = title_score + skill_score + seniority_score + location_score + language_score

    # Penalize if title and skills both look weak.
    if title_score < 12 and skill_score < 10:
        raw_score -= 18
        reasons.append("Weak profile fit")
    elif title_score < 12:
        raw_score -= 8

    # Hard cap for missing required languages such as Japanese-speaking roles.
    if missing_languages:
        raw_score = min(raw_score, 34 if title_score < 20 else 46)

    # Do not let generic remote/customer jobs look like strong matches without real skill/title fit.
    if title_score < 18 and skill_score < 16:
        raw_score = min(raw_score, 49)

    score = max(5, min(96, int(raw_score)))
    if not reasons:
        reasons.append("Review requirements before applying")
    return score, reasons[:4]


def build_role_suggestions(user_titles: List[str], detected_roles_text: str, current_role: str) -> List[str]:
    roles: List[str] = []
    for role in user_titles:
        role = role.strip()
        if role and role not in roles:
            roles.append(role)

    if detected_roles_text:
        for line in detected_roles_text.splitlines():
            candidate = line.replace("-", "").strip()
            if candidate and candidate not in roles:
                roles.append(candidate)

    if current_role and current_role.strip() and current_role.strip() not in roles:
        roles.append(current_role.strip())

    fallback = [
        "Data Analyst",
        "Business Analyst",
        "Reporting Analyst",
        "Operations Analyst",
        "IT Support Specialist",
    ]
    for role in fallback:
        if len(roles) >= 5:
            break
        if role not in roles:
            roles.append(role)

    return roles[:5]

def get_country_market_hint(country_name: str) -> str:
    country = (country_name or "").strip().lower()
    if country == "germany":
        return "German language helps strongly for many local roles, but English-speaking jobs exist in tech, startups, analytics, product, and international companies."
    if country in {"netherlands", "the netherlands"}:
        return "English-speaking roles are more common than in many EU markets, especially in tech, operations, and international business functions."
    if country in {"austria", "switzerland"}:
        return "Local language is often important, especially for customer-facing and traditional companies."
    if country in {"canada", "united states", "united kingdom", "ireland", "australia", "new zealand"}:
        return "English-first roles are common, but local resume style and market positioning still matter."
    return "Target roles with transferable skills first, then adapt your CV and search keywords to local market expectations."


ADZUNA_COUNTRY_CODES = {
    "australia": "au",
    "austria": "at",
    "belgium": "be",
    "brazil": "br",
    "canada": "ca",
    "france": "fr",
    "germany": "de",
    "india": "in",
    "italy": "it",
    "mexico": "mx",
    "netherlands": "nl",
    "the netherlands": "nl",
    "new zealand": "nz",
    "poland": "pl",
    "singapore": "sg",
    "south africa": "za",
    "spain": "es",
    "switzerland": "ch",
    "united kingdom": "gb",
    "uk": "gb",
    "united states": "us",
    "usa": "us",
}

@st.cache_data(show_spinner=False, ttl=900)
def fetch_adzuna_jobs(query: str, country_name: str, location: str = "", limit: int = 24) -> List[Dict]:
    country_code = ADZUNA_COUNTRY_CODES.get((country_name or "").strip().lower())
    app_id = os.getenv("ADZUNA_APP_ID") or get_streamlit_secret("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY") or get_streamlit_secret("ADZUNA_APP_KEY")

    if not country_code or not app_id or not app_key:
        return []

    results: List[Dict] = []
    seen = set()

    for page_no in range(1, 6):
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": "12",
            "what_phrase": query or "",
            "where": location or "",
            "sort_by": "date",
            "content-type": "application/json",
            "max_days_old": "30",
        }

        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page_no}?" + urllib.parse.urlencode(params)

        try:
            payload = http_get_json(url, timeout=12)
        except Exception:
            continue

        items = payload.get("results", []) if isinstance(payload, dict) else []
        if not items:
            continue

        for item in items:
            title = str(item.get("title", "")).strip()
            company_obj = item.get("company") or {}
            company = str(company_obj.get("display_name") if isinstance(company_obj, dict) else company_obj or "").strip()

            location_obj = item.get("location") or {}
            if isinstance(location_obj, dict):
                display_loc = str(location_obj.get("display_name") or "").strip()
            else:
                display_loc = str(location_obj or "").strip()

            redirect_url = str(item.get("redirect_url", "")).strip()
            description = str(item.get("description", "")).strip()
            contract = str(item.get("contract_type", "")).strip()
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary_text = ""
            if salary_min or salary_max:
                salary_text = f"Salary: {salary_min or '—'} to {salary_max or '—'}"

            summary_parts = [x for x in [contract, salary_text, (description[:200] + "...") if description else ""] if x]
            summary = " • ".join(summary_parts)

            key = (title + "|" + company + "|" + display_loc).casefold()
            if title and key not in seen:
                seen.add(key)
                results.append({
                    "source": "Adzuna",
                    "title": title,
                    "company": company or "Employer not shown",
                    "location": display_loc or (location or country_name),
                    "remote": False,
                    "url": redirect_url,
                    "summary": summary
                })
            if len(results) >= limit:
                return results[:limit]

    return results[:limit]

def fetch_live_jobs_global(country_name: str, roles: List[str], location: str = "", user_status: str = "") -> List[Dict]:
    results: List[Dict] = []
    country_lower = (country_name or "").strip().lower()
    search_queries = build_live_job_queries(roles, user_status, max_queries=10, country_name=country_name)

    # Germany has two additional free sources.
    if country_lower == "germany":
        results.extend(fetch_live_jobs_for_germany(roles, location, user_status))

    # Adzuna supports many countries when API keys are configured.
    for query in search_queries:
        results.extend(fetch_adzuna_jobs(query, country_name, location, limit=30))

    # Free global remote source. This keeps worldwide job search useful even without Adzuna keys.
    for query in search_queries[:10]:
        results.extend(fetch_remotive_jobs(query, location, limit=20))

    # Broaden location if exact city/country query produces too few results.
    if len(results) < 15 and location and location.strip().lower() != (country_name or "").strip().lower():
        for query in search_queries[:12]:
            results.extend(fetch_adzuna_jobs(query, country_name, "", limit=30))
            results.extend(fetch_remotive_jobs(query, "", limit=20))

    deduped: List[Dict] = []
    seen = set()
    for item in results:
        key = (item.get("source", "") + "|" + item.get("title", "") + "|" + item.get("company", "") + "|" + item.get("location", "") + "|" + item.get("url", "")).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return sort_jobs_for_user(deduped, user_status, roles, country_name)[:40]


def fallback_job_search_plan(country_name: str, location: str, roles: List[str], cv_text: str) -> Dict:
    best_titles = []
    for role in roles[:5]:
        best_titles.append({
            "title": role,
            "fit_reason": "This matches the transferable skills and positioning suggested by your resume.",
            "seniority": "Junior to Mid-level",
            "english_realistic": "Depends on country and company type"
        })

    search_terms = []
    for role in roles[:4]:
        search_terms.extend([
            f"{role} jobs in {location}",
            f"{role} {country_name} English speaking",
            f"{role} remote {country_name}",
        ])

    return {
        "best_match_titles": best_titles,
        "search_terms": search_terms[:12],
        "market_strategy": [
            get_country_market_hint(country_name),
            f"Start with roles closest to your current profile and apply broadly in {location or country_name}.",
            "Prioritize companies with international teams, clear English-language postings, and realistic entry requirements."
        ],
        "best_live_matches": [],
        "priority_plan": [
            "Apply first to the 10 closest-fit roles.",
            "Use 2 to 3 tailored CV versions for your top role clusters.",
            "Track applications and improve search keywords every 3 to 4 days."
        ],
        "resume_positioning": [
            "Keep your headline aligned to the target role.",
            "Highlight measurable achievements and relevant tools.",
            "Move the most market-relevant skills higher in the CV."
        ],
        "fastest_route": [
            "Apply to 10 to 15 realistic roles this week.",
            "Tailor your CV headline and summary for each role cluster.",
            "Use LinkedIn, Indeed, and the strongest local job board for your country.",
            "Message 3 recruiters or hiring managers where possible.",
            "Practice short interview answers through Work-O-Bot."
        ]
    }

def generate_job_search_plan(country_name: str, location: str, roles: List[str], cv_text: str, live_jobs: List[Dict]) -> Dict:
    prompt = f"""
Return ONLY valid JSON. Do not use markdown.

JSON format:
{{
  "best_match_titles": [
    {{
      "title": "string",
      "fit_reason": "string",
      "seniority": "string",
      "english_realistic": "string"
    }}
  ],
  "search_terms": ["string"],
  "market_strategy": ["string"],
  "best_live_matches": ["string"],
  "priority_plan": ["string"],
  "resume_positioning": ["string"],
  "fastest_route": ["string"]
}}

Country: {country_name}
Preferred location: {location}
Target roles: {roles}

Candidate CV:
{cv_text}

Live jobs:
{live_jobs[:8]}

Rules:
- Be realistic about seniority. Do not suggest mid-senior if the CV does not support it.
- Prefer entry-level or junior recommendations when direct experience is limited.
- Fill every array with useful content.
- best_match_titles must contain exactly 3 items.
- search_terms must contain 4 to 6 items and avoid repetitive variations.
- market_strategy must contain 3 short bullets.
- priority_plan must contain 3 short bullets.
- resume_positioning must contain 3 short bullets.
- fastest_route must contain 3 short bullets.
"""
    result = run_ai_prompt(prompt, force_language=st.session_state.get("preferred_language", "English"), json_mode=True)
    if result.startswith("ERROR:"):
        return fallback_job_search_plan(country_name, location, roles, cv_text)

    try:
        parsed = safe_json_loads(result)
        if not isinstance(parsed, dict) or not parsed.get("best_match_titles"):
            return fallback_job_search_plan(country_name, location, roles, cv_text)
        return parsed
    except Exception:
        return fallback_job_search_plan(country_name, location, roles, cv_text)


# =========================================================
# WORKZO v11.8 - Curated Job Search Assistant
# =========================================================
def extract_top_cv_terms_for_jobs(cv_text: str, max_terms: int = 16) -> List[str]:
    """Small deterministic fallback: extract useful skill/role terms from a CV without pretending they are verified beyond the text."""
    text = (cv_text or "").lower()
    known_terms = [
        "python", "sql", "tableau", "power bi", "excel", "pandas", "numpy", "matplotlib", "seaborn",
        "machine learning", "data analysis", "data visualization", "dashboard", "reporting", "etl", "api",
        "web scraping", "gcp", "aws", "azure", "mysql", "postgresql", "itil", "itsm", "service desk",
        "technical support", "customer support", "incident management", "troubleshooting", "onboarding",
        "customer success", "crm", "salesforce", "hubspot", "jira", "servicenow", "zendesk"
    ]
    terms = []
    for term in known_terms:
        if term in text and term not in terms:
            terms.append(term)
    for token in re.findall(r"\b[A-Z][A-Za-z0-9+#./-]{2,}\b", cv_text or ""):
        cleaned = token.strip(".,:;()[]{}")
        if len(cleaned) > 2 and cleaned.lower() not in {t.lower() for t in terms}:
            if cleaned.lower() not in {"and", "the", "for", "with", "work", "experience", "education"}:
                terms.append(cleaned)
        if len(terms) >= max_terms:
            break
    return terms[:max_terms]


def estimate_years_of_experience_from_cv(cv_text: str) -> int:
    """Best-effort deterministic YoE estimate used only to filter seniority noise."""
    years = set()
    for match in re.findall(r"\b(19\d{2}|20\d{2})\b", cv_text or ""):
        y = int(match)
        if 1980 <= y <= 2035:
            years.add(y)
    if len(years) >= 2:
        return max(0, min(30, max(years) - min(years)))
    m = re.search(r"(\d+)\+?\s*(?:years|yrs|year)\s+(?:of\s+)?experience", (cv_text or "").lower())
    if m:
        return max(0, min(30, int(m.group(1))))
    return 0


def infer_core_job_domain(cv_text: str, roles: Optional[List[str]] = None) -> str:
    blob = " ".join([cv_text or ""] + [str(r) for r in (roles or [])]).lower()
    if any(x in blob for x in ["machine learning", "artificial intelligence", " ai ", "llm", "pytorch", "tensorflow", "data scientist", "ai engineer"]):
        return "ai_data"
    if any(x in blob for x in ["data analyst", "sql", "tableau", "power bi", "dashboard", "analytics"]):
        return "data_analytics"
    if any(x in blob for x in ["technical support", "service desk", "it support", "itsm", "itil", "troubleshooting"]):
        return "it_support"
    if any(x in blob for x in ["frontend", "react", "javascript", "backend", "developer", "software engineer"]):
        return "software"
    return "general"


def build_job_exclusion_terms(cv_text: str, roles: Optional[List[str]] = None, user_status: str = "") -> List[str]:
    """Reject obvious false-positive domains before showing jobs to the user."""
    domain = infer_core_job_domain(cv_text, roles)
    base = ["civil", "mechanical", "electrical design", "cad", "construction", "product design", "industrial design", "graphic design", "fashion", "hardware design"]
    if domain in {"ai_data", "data_analytics"}:
        base += ["product design engineer", "mechanical engineer", "civil engineer", "embedded hardware", "industrial designer"]
    if domain == "it_support":
        base += ["product design", "mechanical", "civil", "architectural", "fashion", "graphic designer"]
    yoe = estimate_years_of_experience_from_cv(cv_text)
    status = (user_status or "").lower()
    if yoe >= 7 or any(x in status for x in ["senior", "experienced"]):
        base += ["intern", "internship", "working student", "trainee", "junior"]
    elif (yoe and yoe <= 2) or any(x in status for x in ["fresh", "entry", "student", "intern"]):
        base += ["principal", "lead", "head of", "director", "senior manager"]
    return list(dict.fromkeys([x.lower() for x in base if x]))[:18]


def infer_job_seniority_from_cv(cv_text: str, user_status: str = "") -> str:
    """Return a conservative seniority label so job search does not drift into wrong levels."""
    blob = f"{cv_text or ''} {user_status or ''}".lower()
    yoe = estimate_years_of_experience_from_cv(cv_text)
    if any(x in blob for x in ["principal", "architect", "head of", "director"]):
        return "lead"
    if yoe >= 7 or any(x in blob for x in ["senior", "experienced professional", "lead"]):
        return "senior"
    if yoe <= 2 and any(x in blob for x in ["fresh", "graduate", "student", "intern", "entry level"]):
        return "entry"
    if any(x in blob for x in ["career changer", "returning", "break"]):
        return "junior"
    return "mid"


def build_precise_job_search_queries(target_roles: List[str], skills: List[str], country_name: str = "", location: str = "", user_status: str = "", cv_text: str = "") -> List[str]:
    """Build short, intentional job queries from target title + top hard skills only.

    Never use the full CV/profile summary as the job-board query; that creates noisy matches.
    """
    roles = [str(r).strip() for r in (target_roles or []) if str(r).strip()]
    skills = [str(s).strip() for s in (skills or []) if str(s).strip()]
    soft = {"teamwork", "leadership", "communication", "time management", "critical thinking", "public relations", "project management", "problem-solving", "problem solving"}
    hard_skills = []
    for skill in skills:
        low = skill.lower()
        if low not in soft and len(low) > 1 and low not in {x.lower() for x in hard_skills}:
            hard_skills.append(skill)
    seniority = infer_job_seniority_from_cv(cv_text, user_status)
    seniority_prefix = {"lead": "Lead", "senior": "Senior", "entry": "Junior", "junior": "Junior", "mid": ""}.get(seniority, "")
    loc = (location or country_name or "").strip()
    queries = []
    for role in roles[:5]:
        role = re.sub(r"\s+", " ", role).strip()
        if not role:
            continue
        title = f"{seniority_prefix} {role}".strip() if seniority_prefix and seniority_prefix.lower() not in role.lower() else role
        top = hard_skills[:3]
        queries.append(" ".join([title] + top + ([loc] if loc else [])).strip())
        queries.append(" ".join([role] + top[:2]).strip())
        if seniority_prefix:
            queries.append(f"{seniority_prefix} {role}".strip())
    return list(dict.fromkeys([q for q in queries if q]))[:10]


def job_domain_allowed(job: Dict, cv_text: str, expansion: Optional[Dict] = None, user_status: str = "") -> Tuple[bool, List[str]]:
    """Hard reject obvious wrong-domain jobs before UI display."""
    expansion = expansion or {}
    job_text = " ".join([str(job.get(k, "")) for k in ["title", "summary", "company", "location", "source"]]).lower()
    roles = expansion.get("job_titles", []) or []
    exclusion_terms = list(expansion.get("exclusion_terms", []) or []) + build_job_exclusion_terms(cv_text, roles, user_status) + user_rejected_job_terms()
    hits = job_hits_exclusion(job, exclusion_terms)
    seniority = infer_job_seniority_from_cv(cv_text, user_status)
    if seniority in {"senior", "lead"} and any(x in job_text for x in ["intern", "internship", "working student", "trainee", "junior"]):
        hits.append("wrong seniority")
    if seniority in {"entry", "junior"} and any(x in job_text for x in ["principal", "director", "head of", "senior manager"]):
        hits.append("wrong seniority")
    return (len(set(hits)) == 0, list(dict.fromkeys(hits))[:8])

def user_rejected_job_terms() -> List[str]:
    feedback = st.session_state.get("job_relevance_feedback", []) or []
    terms = []
    for item in feedback:
        if isinstance(item, dict):
            terms.extend(item.get("terms", []) or [])
            reason = str(item.get("reason", "")).lower()
            title = str(item.get("title", "")).lower()
            if "wrong role" in reason or "domain" in reason:
                terms.extend(re.findall(r"[a-zA-Z][a-zA-Z+.#-]{2,}", title))
    return list(dict.fromkeys([t.lower() for t in terms if len(str(t)) > 2]))[:30]


def job_hits_exclusion(job: Dict, exclusion_terms: Optional[List[str]] = None) -> List[str]:
    job_text = " ".join([str(job.get(k, "")) for k in ["title", "summary", "company", "location", "source"]]).lower()
    hits = []
    for term in (exclusion_terms or []):
        term = str(term or "").lower().strip()
        if term and term in job_text:
            hits.append(term)
    return list(dict.fromkeys(hits))


def fallback_job_query_expansion(cv_text: str, country_name: str, location: str, user_status: str, target_titles: str = "") -> Dict:
    input_titles = [x.strip() for x in (target_titles or "").split(",") if x.strip()]
    inferred_roles = infer_relevant_roles_from_cv(cv_text or "")
    roles = build_role_suggestions(input_titles + inferred_roles, st.session_state.get("suggested_roles_detected", []), st.session_state.get("current_role_detected", ""))[:5]
    if not roles:
        roles = ["Data Analyst", "IT Support Specialist", "Service Desk Analyst"]
    techs = extract_top_cv_terms_for_jobs(cv_text, 10)
    modifiers = get_status_job_modifiers(user_status, country_name)[:4]
    search_queries = build_precise_job_search_queries(roles[:5], techs[:6], country_name, location, user_status, cv_text)
    for role in roles[:3]:
        for mod in modifiers[:2]:
            candidate = f"{mod} {role}"
            if candidate not in search_queries:
                search_queries.append(candidate)
    domain_exclusions = build_job_exclusion_terms(cv_text, roles[:5], user_status)
    return {
        "job_titles": roles[:5],
        "essential_technologies": techs[:8],
        "exclusion_terms": domain_exclusions,
        "search_queries": list(dict.fromkeys(search_queries))[:10],
        "assistant_strategy": [
            "Start with roles closest to your current CV before testing stretch roles.",
            "Use broad role titles first, then narrow by tool keywords and location.",
            "Paste one promising job description into Understand Job before tailoring the CV."
        ]
    }


def generate_job_query_expansion(cv_text: str, country_name: str, location: str, user_status: str, target_titles: str = "") -> Dict:
    """AI-assisted query expansion. Returns titles + technologies, but never adds skills to the CV."""
    fallback = fallback_job_query_expansion(cv_text, country_name, location, user_status, target_titles)
    prompt = f"""
Return ONLY valid JSON. Do not use markdown.

You are a job-search query strategist. Based only on the candidate CV and target country, create better job-search terms.
Do NOT invent experience. Do NOT add missing skills to the CV. Missing skills can be search/learning suggestions only.

JSON format:
{{
  "job_titles": ["string"],
  "essential_technologies": ["string"],
  "exclusion_terms": ["string"],
  "search_queries": ["string"],
  "assistant_strategy": ["string"]
}}

Rules:
- job_titles: 4 to 6 realistic roles, including adjacent titles, not only exact title matches.
- essential_technologies: 5 to 8 technologies/skills actually present or strongly implied by the CV.
- exclusion_terms: 8 to 14 terms for clearly wrong domains/seniority. Example for AI/Data: Product Design, Mechanical, Civil, CAD, Hardware, Internship when senior.
- search_queries: 6 to 10 short job-board queries for {country_name}. Include seniority/status where relevant.
- assistant_strategy: 3 short bullets.
- If the user entered target titles, include them only if realistic.

Target country: {country_name}
Location: {location}
Career status: {user_status}
User requested titles: {target_titles or 'Not specified'}

Candidate CV:
{cv_text[:6000]}
"""
    try:
        try:
            result = run_ai_prompt(prompt, force_language=st.session_state.get("preferred_language", "English"), json_mode=True, temperature=0.1, top_p=0.1)
        except TypeError:
            result = run_ai_prompt(prompt, force_language=st.session_state.get("preferred_language", "English"), json_mode=True)
        parsed = safe_json_loads(result)
        if not isinstance(parsed, dict):
            return fallback
        for key in ["job_titles", "essential_technologies", "exclusion_terms", "search_queries", "assistant_strategy"]:
            if not isinstance(parsed.get(key), list):
                parsed[key] = fallback.get(key, [])
        if not parsed.get("job_titles"):
            parsed["job_titles"] = fallback["job_titles"]
        if not parsed.get("search_queries"):
            parsed["search_queries"] = fallback["search_queries"]
        if not parsed.get("exclusion_terms"):
            parsed["exclusion_terms"] = fallback.get("exclusion_terms", build_job_exclusion_terms(cv_text, parsed.get("job_titles", []), user_status))
        parsed["search_queries"] = build_precise_job_search_queries(
            parsed.get("job_titles", []), parsed.get("essential_technologies", []),
            country_name, location, user_status, cv_text
        ) or fallback.get("search_queries", [])
        return parsed
    except Exception:
        return fallback


def normalize_location_for_job_search(location: str, country_name: str) -> str:
    loc = (location or "").strip()
    if not loc or loc.lower().startswith("anywhere in "):
        return country_name or ""
    aliases = {
        "nyc": "New York",
        "new york city": "New York",
        "the big apple": "New York",
        "sf": "San Francisco",
        "bay area": "San Francisco",
        "munchen": "Munich",
        "munchen": "Munich",
        "koln": "Cologne",
        "nurnberg": "Nuremberg",
        "frankfurt am main": "Frankfurt",
    }
    return aliases.get(loc.lower(), loc)


def estimate_curated_job_alignment(job: Dict, cv_text: str, expansion: Dict, country_name: str = "", user_status: str = "") -> Dict:
    """Deterministic fit estimate. AI can explain later, but the badge should not randomly change."""
    job_text = " ".join([str(job.get(k, "")) for k in ["title", "summary", "company", "location", "source"]]).lower()
    cv_lower = (cv_text or "").lower()
    titles = [str(x).lower() for x in expansion.get("job_titles", [])]
    techs = [str(x).lower() for x in expansion.get("essential_technologies", [])]
    exclusion_terms = [str(x).lower() for x in (expansion.get("exclusion_terms", []) or [])]
    exclusion_terms += user_rejected_job_terms()
    allowed_domain, hard_domain_hits = job_domain_allowed(job, cv_text, expansion, user_status)
    exclusion_hits = list(dict.fromkeys(job_hits_exclusion(job, exclusion_terms) + hard_domain_hits))

    title_hits = []
    for title in titles:
        title_clean = re.sub(r"\s+", " ", title).strip()
        title_words = [w for w in re.findall(r"[a-zA-Z]+", title_clean.lower()) if len(w) > 2]
        if title_clean.lower() in job_text or sum(1 for w in title_words if w in job_text) >= min(2, len(title_words)):
            title_hits.append(title)

    matched_skills = []
    for term in techs:
        if term and term in job_text and term in cv_lower:
            matched_skills.append(term)

    missing_or_stretch = []
    common_required = ["aws", "azure", "power bi", "servicenow", "salesforce", "kubernetes", "docker", "java", "sql", "python", "german", "b1", "b2"]
    for term in common_required:
        if term in job_text and term not in cv_lower:
            missing_or_stretch.append(term)

    score = 45
    score += min(len(title_hits) * 10, 25)
    score += min(len(matched_skills) * 6, 24)
    if exclusion_hits:
        score -= min(40, 18 + len(exclusion_hits) * 7)
    if job.get("remote"):
        score += 3
    text_status = (user_status or "").lower()
    if any(x in text_status for x in ["fresh", "student", "career changer", "returning", "entry"]):
        if any(x in job_text for x in ["senior", "lead", "principal", "manager"]):
            score -= 18
        if any(x in job_text for x in ["junior", "entry", "trainee", "intern", "working student", "graduate", "werkstudent"]):
            score += 14
    score -= min(len(missing_or_stretch) * 5, 18)
    score = max(25, min(96, score))

    if score >= 82:
        badge = "Direct Match"
        badge_color = "Good"
    elif score >= 65:
        badge = "Stretch Role"
        badge_color = "Maybe"
    else:
        badge = "High Effort"
        badge_color = "Risk"

    why = []
    if title_hits:
        why.append(f"Role overlap: {', '.join([x.title() for x in title_hits[:2]])}")
    if matched_skills:
        why.append(f"Skill overlap: {', '.join([x.upper() if len(x)<=3 else x.title() for x in matched_skills[:4]])}")
    if exclusion_hits:
        why.append(f"Filtered risk: {', '.join(exclusion_hits[:3])}")
    if missing_or_stretch:
        why.append(f"Check before applying: {', '.join(missing_or_stretch[:3])}")
    if not why:
        why.append("This is a broader search result; review the JD before tailoring your CV.")

    return {
        "match_score": score,
        "badge": badge,
        "badge_color": badge_color,
        "matched_skills": matched_skills[:6],
        "missing_or_stretch": missing_or_stretch[:6],
        "exclusion_hits": exclusion_hits[:6],
        "assistant_note": " ".join(why[:3])
    }


def curate_job_matches(jobs: List[Dict], cv_text: str, expansion: Dict, country_name: str, user_status: str, limit: int = 18) -> List[Dict]:
    enriched = []
    for job in jobs or []:
        item = dict(job)
        item.update(estimate_curated_job_alignment(item, cv_text, expansion, country_name, user_status))
        allowed, hits = job_domain_allowed(item, cv_text, expansion, user_status)
        if not allowed:
            item["exclusion_hits"] = list(dict.fromkeys((item.get("exclusion_hits") or []) + hits))
            if item.get("match_score", 0) < 75:
                continue
        if item.get("exclusion_hits") and item.get("match_score", 0) < 68:
            continue
        enriched.append(item)
    enriched = sorted(enriched, key=lambda x: x.get("match_score", 0), reverse=True)
    strong = [j for j in enriched if j.get("match_score", 0) >= 60]
    return (strong or enriched)[:limit]


def render_query_expansion_panel(expansion: Dict):
    with st.expander("Search query expansion", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("#### Better role titles")
            for role in expansion.get("job_titles", [])[:6]:
                st.markdown(f"- {html.escape(str(role))}")
        with c2:
            st.markdown("#### Verified CV skills")
            for skill in expansion.get("essential_technologies", [])[:8]:
                st.markdown(f"- {html.escape(str(skill))}")
        with c3:
            st.markdown("#### Exclude noise")
            for term in expansion.get("exclusion_terms", [])[:8]:
                st.markdown(f"- {html.escape(str(term))}")
        with c4:
            st.markdown("#### Search queries")
            for q in expansion.get("search_queries", [])[:8]:
                st.markdown(f"- {html.escape(str(q))}")


def render_curated_job_matches(jobs: List[Dict], country_name: str = ""):
    st.markdown("### Curated job matches")
    if not jobs:
        st.info("Live sources did not return strong matches. Use the search links below, then paste one job description into Understand Job for a precise fit check.")
        return
    st.caption("WorkZo ranks jobs by role overlap, CV skill overlap, seniority risk, and missing stretch skills. Treat scores as guidance, not a guarantee.")
    for idx, job in enumerate(jobs, start=1):
        title = str(job.get("title") or "Job")
        company = str(job.get("company") or "Company not shown")
        location = str(job.get("location") or country_name or "")
        score = int(job.get("match_score", 0) or 0)
        badge = f"{job.get('badge', 'Review')}"
        url = str(job.get("url") or "")
        source = str(job.get("source") or "Source")
        with st.expander(f"{idx}. {title} at {company} — {score}% • {badge}", expanded=(idx <= 3)):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**Location / market:** {html.escape(location)}")
                st.markdown(f"**Source:** {html.escape(source)}")
                if str(source).lower() in ["remotive", "remoteok", "we work remotely", "remote"] or "remote" in str(location).lower():
                    st.caption("Remote note: Please confirm whether this role is worldwide remote or restricted to a country/time zone before applying.")
                st.markdown(f"**Assistant note:** {html.escape(str(job.get('assistant_note', 'Review this JD before tailoring.')))}")
                matched = job.get("matched_skills", []) or []
                missing = job.get("missing_or_stretch", []) or []
                if matched:
                    st.markdown("**Matched from your CV:** " + ", ".join([html.escape(str(x)) for x in matched[:6]]))
                if missing:
                    st.markdown("**Reality check / confirm before adding:** " + ", ".join([html.escape(str(x)) for x in missing[:6]]))
                summary = str(job.get("summary") or "")
                if summary:
                    st.caption(summary[:500])
            with c2:
                if url:
                    st.link_button("Open job", url, use_container_width=True)
                if st.button("Use in Understand Job", key=f"use_job_for_understand_{idx}_{hash(title+company)%99999}", use_container_width=True):
                    jd_seed = f"{title}\nCompany: {company}\nLocation: {location}\nSource: {source}\n\n{job.get('summary','')}\n\nApply URL: {url}"
                    st.session_state["last_understand_job_description"] = jd_seed
                    st.session_state["job_desc_v42"] = jd_seed
                    st.session_state["job_assist_mode_key"] = "understand"
                    st.session_state["page"] = "job_assist"
                    st.session_state["nav_page"] = "job_assist"
                    update_url_page("job_assist")
                    request_scroll_to_top()
                    st.rerun()
                if st.button("Prepare interview", key=f"prep_job_{idx}_{hash(title+company)%99999}", use_container_width=True):
                    jd_seed = f"{title}\nCompany: {company}\nLocation: {location}\n\n{job.get('summary','')}"
                    st.session_state["last_understand_job_description"] = jd_seed
                    st.session_state["interview_job_description"] = jd_seed
                    st.session_state["job_assist_mode_key"] = "prepare"
                    st.session_state["page"] = "job_assist"
                    st.session_state["nav_page"] = "job_assist"
                    update_url_page("job_assist")
                    request_scroll_to_top()
                    st.rerun()
                reason_key = f"reject_reason_{idx}_{hash(title+company)%99999}"
                reject_reason = st.selectbox(
                    "Not relevant because...",
                    ["Wrong role/domain", "Wrong seniority", "Wrong location", "No remote option", "Not my skill set", "Salary too low", "Other"],
                    key=reason_key,
                )
                if st.button("Not Relevant", key=f"reject_job_{idx}_{hash(title+company)%99999}", use_container_width=True):
                    feedback = st.session_state.get("job_relevance_feedback", []) or []
                    terms = re.findall(r"[A-Za-z][A-Za-z+.#-]{2,}", f"{title} {job.get('summary','')}")[:12]
                    feedback.append({"title": title, "company": company, "reason": reject_reason, "terms": terms})
                    st.session_state["job_relevance_feedback"] = feedback[-50:]
                    st.success("Saved. WorkZo will filter similar noisy jobs in this session.")
                    st.rerun()

def render_job_plan(plan: Dict):
    st.markdown("### Roles That Fit Your Profile")
    titles = plan.get("best_match_titles", [])
    if isinstance(titles, list) and titles:
        st.markdown("""
<div class='next-action-card' style='margin-top:6px;'>
  <div class='next-action-label'>Recommended search direction</div>
  <div class='next-action-title'>Choose a role → open job boards → paste one job description → tailor your CV</div>
  <div class='next-action-copy'>WorkZo is strongest when you use it as a journey, not a one-time job list.</div>
</div>
""", unsafe_allow_html=True)
        cols = st.columns(min(3, len(titles[:3])))
        for i, item in enumerate(titles[:3]):
            with cols[i]:
                if isinstance(item, dict):
                    title = str(item.get("title", "Role"))
                    seniority = str(item.get("seniority", "—"))
                    english_realistic = str(item.get("english_realistic", "—"))
                    fit_reason = str(item.get("fit_reason", "—"))
                    keywords = item.get("keywords_to_use", []) or item.get("cv_keywords", []) or []
                    improve_next = item.get("improve_next", "") or item.get("gap", "") or "Add stronger role-specific keywords."
                    fit_score = item.get("fit_score", "") or item.get("score", "") or ""
                    if len(fit_reason) > 170:
                        fit_reason = fit_reason[:170].rsplit(" ", 1)[0] + "..."
                    keyword_text = ", ".join([str(x) for x in keywords[:4]]) if isinstance(keywords, list) else str(keywords)
                    score_html = f"<span class='beta-badge'>{html.escape(str(fit_score))}% role fit</span>" if str(fit_score).strip().isdigit() else ""
                    st.markdown(f"""
<div class='card' style='border-color:rgba(20,184,166,0.28); min-height:300px;'>
  <div class='section-title'>{i+1}. {html.escape(title)}</div>
  <div style='margin:8px 0;'>{score_html}</div>
  <div class='small-muted'>{html.escape(seniority)} • {html.escape(english_realistic)}</div>
  <div style='margin-top:12px;'><b>Why it fits:</b> {html.escape(fit_reason)}</div>
  <div style='margin-top:12px;'><b>Use in CV:</b> {html.escape(keyword_text or title)}</div>
  <div style='margin-top:12px;'><b>Improve next:</b> {html.escape(str(improve_next))}</div>
</div>
""", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='card'><div class='section-title'>{i+1}. {html.escape(str(item))}</div></div>", unsafe_allow_html=True)
    else:
        st.info(txt("no_roles_generated"))

    with st.expander("Search strategy", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"#### {txt('best_search_terms')}")
            for item in plan.get("search_terms", [])[:7]:
                st.markdown(f"- {html.escape(str(item))}")
        with col2:
            st.markdown(f"#### {txt('resume_positioning')}")
            for item in plan.get("resume_positioning", [])[:5]:
                st.markdown(f"- {html.escape(str(item))}")
        with col3:
            st.markdown(f"#### {txt('fastest_route')}")
            for item in plan.get("fastest_route", [])[:5]:
                st.markdown(f"- {html.escape(str(item))}")

    with st.expander("More market strategy", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"#### {txt('market_strategy')}")
            for item in plan.get("market_strategy", [])[:6]:
                st.markdown(f"- {html.escape(str(item))}")
            st.markdown(f"#### {txt('priority_plan')}")
            for item in plan.get("priority_plan", [])[:5]:
                st.markdown(f"- {html.escape(str(item))}")
        with col2:
            best_live = plan.get("best_live_matches", [])
            if best_live:
                st.markdown(f"#### {txt('best_live_matches')}")
                for item in best_live[:5]:
                    item_text = str(item)
                    url_match = re.search(r"https?://\S+", item_text)
                    if url_match:
                        url = url_match.group(0).rstrip(").,]")
                        label = item_text.replace(url_match.group(0), "").strip(" --—") or "Open job"
                        st.markdown(
                            f"- **{html.escape(label)}** — "
                            f"<a class='workzo-link-button' href='{html.escape(url, quote=True)}' target='_blank'>Open job</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"- {html.escape(item_text)}")
            else:
                st.caption("Open the platform search links below to find current postings, then paste one job description into Understand Job.")

