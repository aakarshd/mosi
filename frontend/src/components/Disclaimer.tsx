const SEBI_TEXT =
  'DISCLAIMER: This information is for educational and informational purposes only. ' +
  'It does not constitute investment advice, a recommendation, or a solicitation to ' +
  'buy or sell any securities. MOSI is not a SEBI-registered investment advisor. ' +
  'Past performance is not indicative of future results. Please consult a qualified ' +
  'financial advisor before making any investment decisions. Investments in the ' +
  'securities market are subject to market risks. Read all the related documents ' +
  'carefully before investing.';

export default function Disclaimer() {
  return <div className="disclaimer">{SEBI_TEXT}</div>;
}
