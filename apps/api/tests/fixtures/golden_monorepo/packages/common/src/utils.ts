export const DEFAULT_PAGE_LIMIT = 50;

export function formatUserName(firstName: string, lastName?: string): string {
  if (!lastName) {
    return firstName;
  }
  return `${firstName} ${lastName}`;
}

export const sanitizeEmail = (email: string): string => {
  return email.trim().toLowerCase();
};

