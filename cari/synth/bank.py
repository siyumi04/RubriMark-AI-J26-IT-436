"""Small hand-written question bank: (concept_id, sentence, points). Max score 5 per question."""
QUESTIONS = [
    {"id": "q_photo", "text": "Explain how photosynthesis provides energy for plants.", "concepts": [
        ("k1", "plants absorb sunlight using chlorophyll in the leaves", 2),
        ("k2", "carbon dioxide and water are taken in by the plant", 1),
        ("k3", "glucose is produced and stored as chemical energy", 1),
        ("k4", "oxygen is released as a by product", 1)]},
    {"id": "q_tcp", "text": "Compare TCP and UDP.", "concepts": [
        ("k1", "tcp is connection oriented and establishes a handshake before sending data", 2),
        ("k2", "tcp guarantees reliable ordered delivery using acknowledgements", 1),
        ("k3", "udp is connectionless and sends data without guarantees", 1),
        ("k4", "udp is faster and suits streaming or gaming", 1)]},
    {"id": "q_norm", "text": "Why is database normalization used?", "concepts": [
        ("k1", "normalization reduces data redundancy by splitting tables", 2),
        ("k2", "it prevents update insertion and deletion anomalies", 1),
        ("k3", "relationships are kept using foreign keys", 1),
        ("k4", "it improves data integrity and consistency", 1)]},
    {"id": "q_overfit", "text": "What is overfitting and how can it be reduced?", "concepts": [
        ("k1", "overfitting happens when a model memorises training data and performs badly on new data", 2),
        ("k2", "regularisation penalises model complexity", 1),
        ("k3", "more training data or augmentation improves generalisation", 1),
        ("k4", "cross validation helps detect overfitting", 1)]},
    {"id": "q_supply", "text": "Explain how price is determined in a market.", "concepts": [
        ("k1", "price settles where supply equals demand at the equilibrium point", 2),
        ("k2", "higher demand with fixed supply raises the price", 1),
        ("k3", "a surplus of goods pushes the price down", 1),
        ("k4", "producers supply more when prices are higher", 1)]},
    {"id": "q_mitosis", "text": "Describe the purpose and main stages of mitosis.", "concepts": [
        ("k1", "mitosis produces two identical daughter cells for growth and repair", 2),
        ("k2", "chromosomes are copied before the cell divides", 1),
        ("k3", "chromosomes line up at the middle of the cell during metaphase", 1),
        ("k4", "the cytoplasm splits during cytokinesis", 1)]},
    {"id": "q_stack", "text": "Differentiate between a stack and a queue.", "concepts": [
        ("k1", "a stack follows last in first out order", 2),
        ("k2", "a queue follows first in first out order", 1),
        ("k3", "stack operations are push and pop at the top", 1),
        ("k4", "queue operations are enqueue at the rear and dequeue at the front", 1)]},
    {"id": "q_osmosis", "text": "Define osmosis and state what affects its rate.", "concepts": [
        ("k1", "osmosis is the movement of water across a semipermeable membrane from low to high solute concentration", 2),
        ("k2", "a steeper concentration gradient increases the rate", 1),
        ("k3", "higher temperature speeds up osmosis", 1),
        ("k4", "no energy is required because osmosis is passive", 1)]},
]
