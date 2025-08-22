// Frontend/src/pages/AuthCallback.tsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabase'
import { Loader2, CheckCircle, XCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        const { data, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Auth callback error:', error)
          setError(error.message)
          setLoading(false)
          return
        }

        if (data.session) {
          setSuccess(true)
          setLoading(false)
          
          // Redirect to home page after a brief delay
          setTimeout(() => {
            navigate('/', { replace: true })
          }, 2000)
        } else {
          setError('No session found')
          setLoading(false)
        }
      } catch (error: any) {
        console.error('Unexpected error:', error)
        setError('An unexpected error occurred')
        setLoading(false)
      }
    }

    handleAuthCallback()
  }, [navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-background/50">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
          <h2 className="text-2xl font-semibold text-foreground">Completing authentication...</h2>
          <p className="text-muted-foreground">Please wait while we sign you in.</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-background/50">
        <div className="max-w-md w-full mx-4">
          <Alert variant="destructive" className="mb-4">
            <XCircle className="h-4 w-4" />
            <AlertDescription>
              Authentication failed: {error}
            </AlertDescription>
          </Alert>
          <div className="text-center">
            <button 
              onClick={() => navigate('/')}
              className="text-primary hover:text-primary/80 underline"
            >
              Return to Home
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-background/50">
        <div className="text-center space-y-4">
          <CheckCircle className="w-12 h-12 mx-auto text-green-500" />
          <h2 className="text-2xl font-semibold text-foreground">Welcome to Ani-Match!</h2>
          <p className="text-muted-foreground">Authentication successful. Redirecting you now...</p>
        </div>
      </div>
    )
  }

  return null
}