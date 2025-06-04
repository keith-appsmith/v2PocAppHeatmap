import csv
import datetime
from flask import Flask, render_template, request, send_file, redirect, url_for
from io import StringIO

app = Flask(__name__)

# simple summarization: first sentence or first 20 words
def summarize(text: str) -> str:
    if not text:
        return ''
    parts = text.split('.')
    if parts:
        first = parts[0].strip()
        words = first.split()
        return ' '.join(words[:20]) + ('...' if len(words) > 20 else '')
    return text[:80]


def load_tickets():
    tickets = []
    with open('app/data/tickets.csv', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['CreatedAt'] = datetime.datetime.strptime(row['CreatedAt'], '%Y-%m-%d')
            row['Summary'] = summarize(row['Description'])
            row['Tags'] = tag_ticket(row)
            row['MatchedArticles'] = match_articles(row['Tags'])
            tickets.append(row)
    return tickets


def load_articles():
    articles = []
    with open('app/data/articles.csv', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['Tags'] = row['Tags'].split(';') if row.get('Tags') else []
            articles.append(row)
    return articles


# Initialize articles and tickets after helper functions are defined
ARTICLES = load_articles()

# tag ticket if article keyword appears in subject or description




# tag ticket if article keyword appears in subject or description

def tag_ticket(ticket):
    text = f"{ticket['Subject']} {ticket['Description']}".lower()
    tags = set()
    for article in ARTICLES:
        for tag in article['Tags']:
            if tag.lower() in text:
                tags.add(tag)
    return list(tags)


def match_articles(tags):
    matches = []
    for article in ARTICLES:
        if any(tag in article['Tags'] for tag in tags):
            matches.append(article)
    return matches

# Load tickets after helper functions are available
TICKETS = load_tickets()


def filter_tickets(tickets, params):
    filtered = []
    start = params.get('start')
    end = params.get('end')
    for t in tickets:
        if params.get('product') and t['Product'] != params['product']:
            continue
        if params.get('region') and t['Region'] != params['region']:
            continue
        if params.get('agent') and t['Agent'] != params['agent']:
            continue
        if params.get('team') and t['Team'] != params['team']:
            continue
        if start and t['CreatedAt'] < datetime.datetime.fromisoformat(start):
            continue
        if end and t['CreatedAt'] > datetime.datetime.fromisoformat(end):
            continue
        filtered.append(t)
    return filtered


def tag_stats(tickets):
    counts = {}
    for t in tickets:
        for tag in t['Tags']:
            counts[tag] = counts.get(tag, 0) + 1
    return counts


@app.route('/')
def index():
    params = request.args
    filtered = filter_tickets(TICKETS, params)
    stats = tag_stats(filtered)
    return render_template('index.html', tickets=filtered, articles=ARTICLES, stats=stats, params=params)


@app.route('/export')
def export_csv():
    params = request.args
    filtered = filter_tickets(TICKETS, params)
    csvfile = StringIO()
    fieldnames = ['TicketID', 'Product', 'Region', 'Agent', 'Team', 'CreatedAt', 'Subject', 'Summary', 'Tags', 'MatchedArticles']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for t in filtered:
        writer.writerow({
            'TicketID': t['TicketID'],
            'Product': t['Product'],
            'Region': t['Region'],
            'Agent': t['Agent'],
            'Team': t['Team'],
            'CreatedAt': t['CreatedAt'].strftime('%Y-%m-%d'),
            'Subject': t['Subject'],
            'Summary': t['Summary'],
            'Tags': ';'.join(t['Tags']),
            'MatchedArticles': ';'.join(a['Title'] for a in t['MatchedArticles'])
        })
    csvfile.seek(0)
    return send_file(csvfile, mimetype='text/csv', as_attachment=True, download_name='tickets.csv')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
