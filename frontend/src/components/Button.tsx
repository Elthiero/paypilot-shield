import type { ButtonHTMLAttributes } from "react";

const CLS = { primary: "btn-primary", brand: "btn-brand", secondary: "btn-secondary", danger: "btn-danger", chip: "btn-chip" } as const;

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof CLS;
  loading?: boolean;
}

export default function Button({ variant = "primary", loading, disabled, children, className = "", ...rest }: Props) {
  return (
    <button className={`${CLS[variant]} ${className}`} disabled={disabled || loading} {...rest}>
      {loading && <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" aria-hidden />}
      {children}
    </button>
  );
}
