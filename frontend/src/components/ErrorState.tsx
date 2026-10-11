import Banner from "./Banner";
import Button from "./Button";

export default function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Banner kind="error" title="Something went wrong" action={onRetry && <Button variant="secondary" onClick={onRetry}>Try again</Button>}>
      {message}
    </Banner>
  );
}
