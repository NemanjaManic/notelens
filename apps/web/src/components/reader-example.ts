// Curated display content only. This example does not represent a service result.
export const cardiologyExample = {
  id: 'cardiology',
  title: 'Cardiology follow-up',
  subtitle: 'Synthetic outpatient note',
  sections: [
    { heading: 'Reason for visit', text: 'Follow-up for occasional palpitations.' },
    { heading: 'History', text: 'The patient describes brief episodes of a racing heartbeat. No chest pain or shortness of breath was reported.' },
    { heading: 'Investigations', text: 'A 12-lead ECG was performed during the visit. The tracing showed normal sinus rhythm.' },
  ],
  annotation: {
    title: 'Normal sinus rhythm',
    text: 'The ECG recorded the heart beating in its usual rhythm.',
    quote: 'normal sinus rhythm',
  },
} as const;

export const cardiologyText = cardiologyExample.sections.map(section => `${section.heading}\n${section.text}`).join('\n\n');
const start = Array.from(cardiologyText.slice(0, cardiologyText.indexOf(cardiologyExample.annotation.quote))).length;
export const cardiologySpan = { start, end: start + Array.from(cardiologyExample.annotation.quote).length,
  quote: cardiologyExample.annotation.quote };
