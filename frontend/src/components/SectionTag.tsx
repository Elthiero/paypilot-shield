export default function SectionTag({ children }: { children: string }) {
  return <p className="inline-block bg-card border border-ink rounded-tag px-3 font-hand font-bold text-[26px] leading-9">{children}</p>;
}
