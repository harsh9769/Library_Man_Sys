from app import app, db, Books,Data

# Create an application context
with app.app_context():
    # Query all books from the database
    data = Data.query.all()
    
    # Print out the results
    print(data)
