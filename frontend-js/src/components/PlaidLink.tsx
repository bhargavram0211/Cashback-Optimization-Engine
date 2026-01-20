import React, { useEffect, useCallback } from 'react';
import { usePlaidLink } from 'react-plaid-link';
import type { 
  PlaidLinkOnSuccessMetadata, 
  PlaidLinkOnExitMetadata,
  PlaidLinkExitReason 
} from '../types';

interface PlaidLinkProps {
  linkToken: string | null;
  onSuccess: (publicToken: string, metadata: PlaidLinkOnSuccessMetadata) => void | Promise<void>;
  onExit?: (err: Error | null, metadata: PlaidLinkOnExitMetadata | null) => void;
  onEvent?: (eventName: string, metadata: Record<string, any>) => void;
}

/**
 * PlaidLink Component
 * 
 * Wrapper component for Plaid Link SDK that handles initialization,
 * callbacks, and error handling.
 */
export const PlaidLink: React.FC<PlaidLinkProps> = ({
  linkToken,
  onSuccess,
  onExit,
  onEvent,
}) => {
  const onSuccessCallback = useCallback(
    (publicToken: string, metadata: PlaidLinkOnSuccessMetadata) => {
      console.log('[PlaidLink] onSuccess:', { publicToken, metadata });
      onSuccess(publicToken, metadata);
    },
    [onSuccess]
  );

  const onExitCallback = useCallback(
    (err: Error | null, metadata: PlaidLinkOnExitMetadata | null) => {
      console.log('[PlaidLink] onExit:', { err, metadata });
      
      if (onExit) {
        onExit(err, metadata);
      } else {
        // Default error handling
        if (err) {
          console.error('[PlaidLink] Error:', err);
        }
        if (metadata?.status) {
          console.log('[PlaidLink] Exit status:', metadata.status);
        }
      }
    },
    [onExit]
  );

  const onEventCallback = useCallback(
    (eventName: string, metadata: Record<string, any>) => {
      console.log('[PlaidLink] Event:', eventName, metadata);
      if (onEvent) {
        onEvent(eventName, metadata);
      }
    },
    [onEvent]
  );

  const { open, ready } = usePlaidLink({
    token: linkToken || null,
    onSuccess: onSuccessCallback,
    onExit: onExitCallback,
    onEvent: onEventCallback,
  });

  // Auto-open Link when ready
  useEffect(() => {
    if (ready && linkToken) {
      open();
    }
  }, [ready, linkToken, open]);

  // This component doesn't render anything visible
  // It just manages the Plaid Link flow
  return null;
};

/**
 * Helper function to get user-friendly error message from Plaid Link exit
 */
export function getPlaidExitErrorMessage(
  err: Error | null,
  metadata: PlaidLinkOnExitMetadata | null
): string {
  if (err) {
    return `Connection error: ${err.message}`;
  }

  if (!metadata || !metadata.status) {
    return 'Connection was closed. Please try again.';
  }

  const status = metadata.status as PlaidLinkExitReason;

  switch (status) {
    case 'USER_EXIT':
      return 'You closed the connection window. No bank was connected.';
    
    case 'INSTITUTION_ERROR':
      return 'There was an error connecting to your bank. Please try again or select a different bank.';
    
    case 'INVALID_CREDENTIALS':
      return 'The username or password you entered is incorrect. Please try again.';
    
    case 'ITEM_LOGIN_REQUIRED':
      return 'Your bank requires you to log in again. Please reconnect your account.';
    
    case 'RATE_LIMIT_EXCEEDED':
      return 'Too many connection attempts. Please wait a few minutes and try again.';
    
    case 'USER_PERMISSION_DENIED':
      return 'You did not grant the necessary permissions. Please try again and allow access.';
    
    case 'USER_OAUTH_ACTION_REQUIRED':
      return 'Additional action is required to complete the connection. Please follow the instructions in the popup.';
    
    case 'ERROR':
      return 'An unexpected error occurred. Please try again.';
    
    default:
      return `Connection failed: ${status}. Please try again.`;
  }
}
