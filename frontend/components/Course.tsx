"use client";
import { ArrowRight } from "lucide-react";
export default function Course({
  color,
  symbol,
  label,
  title,
  text,
  footer,
  onClick,
  pending = false,
}: {
  color: string;
  symbol: string;
  label: string;
  title: string;
  text: string;
  footer: string;
  onClick: () => void;
  pending?: boolean;
}) {
  return (
    <button className="course" onClick={onClick}>
      <div className={"course-art " + color}>
        <span>{symbol}</span>
        <div className="course-arc" />
        <span className="small-star">✳</span>
        {pending && <span className="soon">Bientôt</span>}
      </div>
      <div className="course-content">
        <div className="eyebrow">{label}</div>
        <h3>{title}</h3>
        <p>{text}</p>
        <div className="course-footer">
          {footer}
          <ArrowRight size={17} />
        </div>
      </div>
    </button>
  );
}
