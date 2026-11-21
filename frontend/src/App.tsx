import SessionProvider from './contexts/SessionProvider'
import AppRoutes from './routes/AppRoutes'

export default function App() {
  return <SessionProvider><AppRoutes /></SessionProvider>
}
