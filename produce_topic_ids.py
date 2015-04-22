import json

if __name__ == '__main__':
    with open('../bitetheballot-topics.json', 'r') as f:
        topics = json.load(f)
        topic_ids = []
        for topic_id, topic in topics.items():
            for statement_id, statement in topic['statements'].items():
                topic_ids.append("{0}_{1}".format(topic_id, statement_id))
        topic_ids.sort()
        print(topic_ids)
