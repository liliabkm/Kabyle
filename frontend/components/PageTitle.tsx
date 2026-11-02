"use client";
export default function PageTitle({
  tag,
  title,
  text,
}: {
  tag: string;
  title: string;
  text: string;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{tag}</div>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
    </div>
  );
}
