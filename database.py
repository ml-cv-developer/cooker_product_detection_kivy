import mysql.connector


class ClassMySQL:

    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self, host, database, user, password):
        try:
            self.connection = None
            self.cursor = None
            self.connection = mysql.connector.connect(host=host, database=database, user=user, password=password)
            self.cursor = self.connection.cursor()
        except mysql.connector.Error as error:
            print("Failed to connect database! {}".format(error))

    def commit(self, table, cam_ind, count, timestamp):
        if self.connection is None:
            return

        try:
            query = "INSERT INTO {} (camera_id, count, datetime) VALUES ({}, {}, '{}')".\
                format(table, cam_ind, count, timestamp)
            print(query)
            self.cursor.execute(query)
            self.connection.commit()
        except mysql.connector.Error as error:
            print("Failed to insert data to table! {}".format(error))

    def disconnect(self):
        if self.cursor is not None:
            self.cursor.close()

        if self.connection is not None:
            self.connection.close()


if __name__ == '__main__':
    class_db = ClassMySQL()
    class_db.connect()
    class_db.commit(1, 14, '2019-08-14 12:24:20')
    class_db.commit(2, 10, '2019-05-14 12:24:20')
