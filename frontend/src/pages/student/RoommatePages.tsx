import { MapPin } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import { Badge, Empty, Field, Heading } from '../../components/common/UI'
import { Paging, Result } from '../../components/common/ApiUI'
import ContactButton from '../../components/common/ContactButton'
import ReportButton from '../../components/common/ReportButton'
import { useSession } from '../../contexts/SessionContext'
import { useApi } from '../../hooks/useApi'
import { ApiError, apiRequest, payload } from '../../services/api'
import type { ApiPage } from '../../services/api'
import { areas, levels, lifestyles, money } from '../../utils/catalogue'

type Roommate = { id: string; display_name: string; preferred_area: string; budget_min: string; budget_max: string; student_level: string; lifestyle_preferences: string[]; description: string; visibility: string; moderation_hidden: boolean; compatibility: number }

function ProfileSummary({ profile }: { profile: Roommate }) {
  return <><span className="avatar roommate-avatar" aria-hidden="true">{profile.display_name.slice(0, 2).toUpperCase()}</span>
    <h2>{profile.display_name}</h2><p className="muted">Level {profile.student_level}</p><p className="row"><MapPin size={16} />{profile.preferred_area}</p>
    <p className="price">{money(Number(profile.budget_min))}–{money(Number(profile.budget_max))} <small>/ semester</small></p>
    <div className="row">{profile.lifestyle_preferences.map(item => <Badge key={item}>{item}</Badge>)}</div></>
}

export function Roommates({ student = false }: { student?: boolean }) {
  const { token, account } = useSession()
  const [query, setQuery] = useSearchParams()
  const number = Math.max(1, Number(query.get('page')) || 1)
  const list = useApi<ApiPage<Roommate>>(`roommates/?${query}`, token)
  const base = student ? '/student/roommates' : '/roommates'
  function change(key: string, value: string) {
    setQuery(previous => {
      const next = new URLSearchParams(previous)
      if (key !== 'page') next.delete('page')
      if (value) next.set(key, value)
      else next.delete(key)
      return next
    }, { replace: true })
  }
  return <div className={student ? '' : 'wrap section'}><Heading title="Find a Roommate" text="Matches are ranked using overlapping budgets, preferred areas and shared lifestyle preferences." action={account?.role === 'student' && <Link className="btn primary" to="/student/roommates/setup">My roommate profile</Link>} />
    <div className="panel filter-panel open"><div className="filter-grid">
      <Field label="Maximum budget (GH₵)"><input type="number" min="0" step=".01" value={query.get('max') ?? ''} onChange={event => change('max', event.target.value)} /></Field>
      <Field label="Preferred area"><select value={query.get('area') ?? ''} onChange={event => change('area', event.target.value)}><option value="">All areas</option>{areas.map(item => <option key={item}>{item}</option>)}</select></Field>
      <Field label="Study level"><select value={query.get('level') ?? ''} onChange={event => change('level', event.target.value)}><option value="">All levels</option>{levels.map(item => <option key={item}>{item}</option>)}</select></Field>
      <Field label="Lifestyle"><select value={query.get('lifestyle') ?? ''} onChange={event => change('lifestyle', event.target.value)}><option value="">All preferences</option>{lifestyles.map(item => <option key={item}>{item}</option>)}</select></Field>
    </div></div>
    <Result loading={list.loading} error={list.error}>
      {list.data?.results.length === 0 && <Empty title="No matching profiles" />}
      <div className="cards-grid">{list.data?.results.map(profile => <article className="panel roommate-card" key={profile.id}><ProfileSummary profile={profile} />
        <div className="row"><Link className="btn outline" to={`${base}/${profile.id}`}>View Profile</Link><ContactButton target="roommate" id={profile.id} label="Message Roommate" /></div>
      </article>)}</div>
      <Paging page={list.data} number={number} change={page => change('page', String(page))} />
    </Result>
  </div>
}

export function RoommateDetail({ student = false }: { student?: boolean }) {
  const { id } = useParams()
  const { token } = useSession()
  const profile = useApi<Roommate>(id ? `roommates/${id}/` : undefined, token)
  return <div className={student ? '' : 'wrap section'}><Link className="text-link back-link" to={student ? '/student/roommates' : '/roommates'}>← Back to roommates</Link>
    <Result loading={profile.loading} error={profile.error}>{profile.data && <article className="panel roommate-card">
      <ProfileSummary profile={profile.data} /><p>{profile.data.description}</p><ContactButton target="roommate" id={profile.data.id} label="Message Roommate" /><ReportButton target="roommate" id={profile.data.id} />
    </article>}</Result>
  </div>
}

export function RoommateSetup() {
  const { token } = useSession()
  const profile = useApi<Roommate>('roommates/me/', token)
  const missing = profile.error instanceof ApiError && profile.error.status === 404
  return <><Heading title="Roommate profile" text="Choose what is visible to other students." />
    <Result loading={profile.loading} error={missing ? undefined : profile.error}>
      {token && (profile.data || missing) && <ProfileForm profile={profile.data} token={token} />}
    </Result>
  </>
}

function ProfileForm({ profile, token }: { profile?: Roommate; token: string }) {
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  return <form className="panel padded stack form-width" onSubmit={async event => {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const fields = { ...Object.fromEntries(data), lifestyle_preferences: data.getAll('lifestyle_preferences') }
    setError(''); setNotice('')
    if (Number(data.get('budget_min')) > Number(data.get('budget_max'))) { setError('Minimum budget must not exceed maximum budget.'); return }
    setBusy(true)
    try { await apiRequest('roommates/me/', payload('PUT', fields), token); setNotice('Profile saved.') }
    catch (error) { setError(error instanceof Error ? error.message : 'Profile could not be saved.') }
    finally { setBusy(false) }
  }}>
    {profile?.moderation_hidden && <p className="notice" role="status">This profile is hidden from discovery by moderation.</p>}
    <div className="two-grid">
      <Field label="Display name"><input name="display_name" required maxLength={100} defaultValue={profile?.display_name} /></Field>
      <Field label="Study level"><select name="student_level" defaultValue={profile?.student_level}>{levels.map(item => <option key={item}>{item}</option>)}</select></Field>
      <Field label="Preferred area"><input name="preferred_area" required maxLength={100} defaultValue={profile?.preferred_area} /></Field>
      <Field label="Visibility"><select name="visibility" defaultValue={profile?.visibility ?? 'private'}><option value="private">Private</option><option value="public">Public</option></select></Field>
      <Field label="Minimum budget (GH₵)"><input name="budget_min" type="number" min="0" step=".01" required defaultValue={profile?.budget_min} /></Field>
      <Field label="Maximum budget (GH₵)"><input name="budget_max" type="number" min="0" step=".01" required defaultValue={profile?.budget_max} /></Field>
    </div>
    <fieldset className="checks"><legend>Lifestyle preferences</legend>{lifestyles.map(item => <label key={item}><input name="lifestyle_preferences" type="checkbox" value={item} defaultChecked={profile?.lifestyle_preferences.includes(item)} />{item}</label>)}</fieldset>
    <Field label="Short introduction"><textarea name="description" rows={4} maxLength={1500} defaultValue={profile?.description} /></Field>
    {error && <p role="alert" className="notice error">{error}</p>}{notice && <p role="status" className="notice">{notice}</p>}
    <div className="row"><button className="btn primary" disabled={busy}>Save profile</button><Link className="btn outline" to="/student/roommates">Back to roommates</Link></div>
  </form>
}
