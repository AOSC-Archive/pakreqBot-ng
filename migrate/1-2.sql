.print 'Updating placeholders for descriptions...'

UPDATE request SET description = 'N/A' WHERE description = 'Unavailable';

.print 'Migration finished!'