export default function SectionCard({
  title,
  description,
  children,
  className = "",
}: {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`surface-card p-6 ${className}`}>
      {title ? (
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      ) : null}
      {description ? (
        <p className="mt-1 text-sm text-slate-600">{description}</p>
      ) : null}
      <div className={title || description ? "mt-4" : ""}>{children}</div>
    </section>
  );
}
