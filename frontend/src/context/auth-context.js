import {createContext} from 'react';

// The shared context is outside the component module so Fast Refresh remains safe.
export const AuthContext=createContext(null);
