'use client';

import { useMemo } from 'react';
import { ClerkProvider } from '@clerk/nextjs';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { useCruseStore } from '@/store/cruseStore';
import './globals.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const darkMode = useCruseStore((s) => s.darkMode);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: darkMode ? 'dark' : 'light',
          primary: { main: '#3b82f6' },
          secondary: { main: '#8b5cf6' },
          background: {
            default: darkMode ? '#0f172a' : '#f8fafc',
            paper: darkMode ? '#1e293b' : '#ffffff',
          },
        },
        typography: {
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        },
        shape: { borderRadius: 12 },
        components: {
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: 'none',
                fontWeight: 600,
                borderRadius: 10,
              },
            },
          },
          MuiTextField: {
            defaultProps: { variant: 'outlined', size: 'small' },
          },
          MuiOutlinedInput: {
            styleOverrides: {
              root: {
                backgroundColor: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.02)',
                backdropFilter: 'blur(8px)',
                borderRadius: 10,
                transition: 'background-color 0.2s ease, box-shadow 0.2s ease',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
                  transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: darkMode ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.15)',
                },
                '&.Mui-focused': {
                  backgroundColor: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(59,130,246,0.03)',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#3b82f6',
                  boxShadow: '0 0 12px rgba(59,130,246,0.25), 0 0 4px rgba(59,130,246,0.1)',
                },
              },
            },
          },
          MuiInputLabel: {
            styleOverrides: {
              root: {
                '&.Mui-focused': {
                  color: '#3b82f6',
                },
              },
            },
          },
          MuiSelect: {
            styleOverrides: {
              root: {
                borderRadius: 10,
              },
            },
          },
          MuiFormControlLabel: {
            styleOverrides: {
              root: {
                borderRadius: 8,
                padding: '2px 8px',
                marginLeft: -8,
                transition: 'background-color 0.2s ease',
                '&:hover': {
                  backgroundColor: darkMode ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.02)',
                },
              },
            },
          },
          MuiRadio: {
            styleOverrides: {
              root: {
                '&.Mui-checked': {
                  color: '#3b82f6',
                },
              },
            },
          },
          MuiCheckbox: {
            styleOverrides: {
              root: {
                '&.Mui-checked': {
                  color: '#3b82f6',
                },
              },
            },
          },
          MuiSlider: {
            styleOverrides: {
              root: {
                color: '#3b82f6',
              },
              thumb: {
                boxShadow: '0 0 8px rgba(59,130,246,0.4)',
                '&:hover, &.Mui-active': {
                  boxShadow: '0 0 14px rgba(59,130,246,0.6)',
                },
              },
              track: {
                background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                border: 'none',
              },
            },
          },
        },
      }),
    [darkMode]
  );

  return (
    <ClerkProvider>
      <html lang="en" data-theme={darkMode ? 'dark' : 'light'}>
        <head>
          <link
            rel="stylesheet"
            href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          />
        </head>
        <body>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              {children}
            </LocalizationProvider>
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
