import { Link, Route, Routes } from 'react-router'
import { Empty } from '../components/common/UI'
import AdminLayout from '../components/layout/AdminLayout'
import ManagerLayout from '../components/layout/ManagerLayout'
import PublicLayout from '../components/layout/PublicLayout'
import StudentLayout from '../components/layout/StudentLayout'
import Messages from '../components/messaging/Messages'
import AdminPage from '../pages/admin/AdminPage'
import { AuthPage } from '../pages/auth/AuthPages'
import { ManagerHostelPage, ManagerListings } from '../pages/manager/LiveHostels'
import PromotionsPage from '../pages/manager/PromotionsPage'
import PricingPage from '../pages/public/PricingPage'
import ManagerPage from '../pages/manager/ManagerPage'
import HomePage from '../pages/public/HomePage'
import { HostelDetails, HostelDirectory } from '../pages/public/HostelPages'
import { HelpPage, ProfileSettings } from '../pages/public/SupportPages'
import { RoommateDetail, Roommates, RoommateSetup } from '../pages/student/RoommatePages'
import StudentPage from '../pages/student/StudentPage'

export default function AppRoutes() {
  return <Routes>
    <Route element={<PublicLayout />}>
      <Route index element={<HomePage />} />
      <Route path="hostels" element={<HostelDirectory />} />
      <Route path="pricing" element={<PricingPage />} />
      <Route path="hostels/:id" element={<HostelDetails />} />
      <Route path="roommates" element={<Roommates />} />
      <Route path="roommates/:id" element={<RoommateDetail />} />
      <Route path="login" element={<AuthPage key="login" mode="login" />} />
      <Route path="register" element={<AuthPage key="register" mode="register" />} />
      <Route path="onboarding/student" element={<AuthPage key="onboard-student" mode="register" />} />
      <Route path="onboarding/manager" element={<AuthPage key="onboard-manager" mode="register" startingRole="manager" />} />
      <Route path="help" element={<HelpPage />} />
      <Route path="*" element={<div className="wrap section"><Empty title="Page not found" action={<Link className="btn primary" to="/">Back to home</Link>} /></div>} />
    </Route>
    <Route path="student" element={<StudentLayout />}>
      <Route index element={<StudentPage />} />
      <Route path="hostels" element={<HostelDirectory key="student-hostels" student />} />
      <Route path="hostels/:id" element={<HostelDetails student />} />
      <Route path="roommates" element={<Roommates student />} />
      <Route path="roommates/setup" element={<RoommateSetup />} />
      <Route path="roommates/:id" element={<RoommateDetail student />} />
      <Route path="messages/:id?" element={<Messages role="student" />} />
      <Route path="saved" element={<HostelDirectory key="saved" student saved />} />
      <Route path="profile" element={<ProfileSettings />} />
      <Route path="help" element={<HelpPage workspace />} />
    </Route>
    <Route path="manager" element={<ManagerLayout />}>
      <Route index element={<ManagerPage />} />
      <Route path="hostels" element={<ManagerListings />} />
      <Route path="hostels/new" element={<ManagerHostelPage mode="new" />} />
      <Route path="hostels/:id/edit" element={<ManagerHostelPage mode="edit" />} />
      <Route path="hostels/:id/rooms" element={<ManagerHostelPage mode="rooms" />} />
      <Route path="hostels/:id/availability" element={<ManagerHostelPage mode="availability" />} />
      <Route path="hostels/:id/photos" element={<ManagerHostelPage mode="photos" />} />
      <Route path="hostels/:id/preview" element={<ManagerHostelPage mode="preview" />} />
      <Route path="availability" element={<ManagerListings key="availability" availability />} />
      <Route path="messages/:id?" element={<Messages role="manager" />} />
      <Route path="subscription" element={<PromotionsPage />} />
      <Route path="profile" element={<ProfileSettings />} />
      <Route path="help" element={<HelpPage workspace />} />
    </Route>
    <Route path="admin" element={<AdminLayout />}>
      <Route index element={<AdminPage />} />
      <Route path="users" element={<AdminPage key="users" section="users" />} />
      <Route path="listings" element={<AdminPage key="listings" section="listings" />} />
      <Route path="verification" element={<AdminPage key="verification" section="verification" />} />
      <Route path="moderation" element={<AdminPage key="moderation" section="moderation" />} />
      <Route path="help" element={<HelpPage workspace />} />
    </Route>
  </Routes>
}
