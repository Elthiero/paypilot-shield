export default function SectionTag({ id, children }: { id?: string; children: string }) {
  return <h2 id={id} className="inline-block bg-card border border-ink rounded-tag px-3 font-hand font-bold text-[26px] leading-9">{children}</h2>;
}
