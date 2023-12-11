import time

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        self.chain.append(genesis_block)

    def add_block(self, block):
        if self.is_valid_block(block, self.chain[-1]):
            self.chain.append(block)

    @staticmethod
    def is_valid_block(block, previous_block):
        if block.previous_hash != previous_block.hash:
            return False
        if block.compute_hash() != block.hash:
            return False
        return True
