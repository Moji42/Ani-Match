// Frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react'
import { useToast } from '@/hooks/use-toast'
import { supabase, User, Session } from '@/lib/supabase'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signInWithGoogle: () => Promise<void>
  signInWithGitHub: () => Promise<void>
  signInWithEmail: (email: string, password: string) => Promise<void>
  signUpWithEmail: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
  // Get initial session
  const getInitialSession = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    setSession(session)
    setUser(session?.user ?? null)
    setLoading(false)
  }

  getInitialSession()

  // Listen for auth changes
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange(async (event, session) => {
    setSession(session)
    setUser(session?.user ?? null)
    setLoading(false)

    // Use a type guard to handle the event safely
    if (event === 'SIGNED_IN') {
      toast({
        title: "Welcome back!",
        description: "You've been successfully signed in.",
      })
    } else if (event === 'SIGNED_OUT') {
      toast({
        title: "Signed out",
        description: "You've been successfully signed out.",
      })
    } else if (event === 'USER_UPDATED') {
      // Handle sign up success with USER_UPDATED event instead of SIGNED_UP
      toast({
        title: "Account created!",
        description: "Please check your email to verify your account.",
      })
    }
  })

  return () => subscription.unsubscribe()
}, [toast])

  const signInWithGoogle = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
      
      if (error) throw error
    } catch (error: any) {
      toast({
        title: "Authentication Error",
        description: error.message || "Failed to sign in with Google",
        variant: "destructive"
      })
    }
  }

  const signInWithGitHub = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
      
      if (error) throw error
    } catch (error: any) {
      toast({
        title: "Authentication Error",
        description: error.message || "Failed to sign in with GitHub",
        variant: "destructive"
      })
    }
  }

  const signInWithEmail = async (email: string, password: string) => {
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password
      })
      
      if (error) throw error
    } catch (error: any) {
      toast({
        title: "Authentication Error",
        description: error.message || "Failed to sign in",
        variant: "destructive"
      })
      throw error
    }
  }

  const signUpWithEmail = async (email: string, password: string) => {
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`
        }
      })
      
      if (error) throw error
    } catch (error: any) {
      toast({
        title: "Authentication Error",
        description: error.message || "Failed to create account",
        variant: "destructive"
      })
      throw error
    }
  }

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to sign out",
        variant: "destructive"
      })
    }
  }

  const resetPassword = async (email: string) => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`
      })
      
      if (error) throw error
      
      toast({
        title: "Password reset sent",
        description: "Check your email for password reset instructions."
      })
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to send password reset email",
        variant: "destructive"
      })
      throw error
    }
  }

  const value = {
    user,
    session,
    loading,
    signInWithGoogle,
    signInWithGitHub,
    signInWithEmail,
    signUpWithEmail,
    signOut,
    resetPassword
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}