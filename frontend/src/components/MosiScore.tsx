export default function MosiScore({ score }: { score: number }) {
  let cls = 'score score--low';
  if (score >= 70) cls = 'score score--high';
  else if (score >= 40) cls = 'score score--medium';

  return <span className={cls}>{score.toFixed(1)}</span>;
}
