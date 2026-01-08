import { useState, useEffect, useRef } from 'react';
import { ALL_SYMBOLS } from '../constants/stocks';
import './StockSearchInput.css';

const StockSearchInput = ({ 
  value = '', 
  onChange, 
  placeholder = 'Search by symbol or company name...',
  required = false,
  disabled = false 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);

  // Initialize search term from value prop
  useEffect(() => {
    if (value) {
      const stock = ALL_SYMBOLS.find(s => s.value === value);
      if (stock) {
        setSearchTerm(`${stock.label} - ${stock.name}`);
      } else {
        setSearchTerm(value);
      }
    }
  }, [value]);

  // Filter stocks based on search term
  useEffect(() => {
    if (searchTerm.length > 0) {
      const term = searchTerm.toLowerCase();
      const filtered = ALL_SYMBOLS.filter(stock => 
        stock.label.toLowerCase().includes(term) ||
        stock.name.toLowerCase().includes(term) ||
        stock.value.toLowerCase().includes(term)
      );
      setFilteredStocks(filtered.slice(0, 10)); // Limit to 10 results
    } else {
      setFilteredStocks([]);
    }
  }, [searchTerm]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setSearchTerm(newValue);
    setShowDropdown(true);
    setSelectedIndex(-1);
    
    // If user clears input, clear the selection
    if (newValue === '') {
      onChange('');
    }
  };

  const handleStockSelect = (stock) => {
    setSearchTerm(`${stock.label} - ${stock.name}`);
    setShowDropdown(false);
    onChange(stock.value);
  };

  const handleKeyDown = (e) => {
    if (!showDropdown || filteredStocks.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < filteredStocks.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < filteredStocks.length) {
          handleStockSelect(filteredStocks[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };

  const handleFocus = () => {
    if (searchTerm.length > 0) {
      setShowDropdown(true);
    }
  };

  return (
    <div className="stock-search-input" ref={dropdownRef}>
      <input
        ref={inputRef}
        type="text"
        value={searchTerm}
        onChange={handleInputChange}
        onFocus={handleFocus}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className="stock-search-field"
        autoComplete="off"
      />
      
      {showDropdown && filteredStocks.length > 0 && (
        <div className="stock-search-dropdown">
          {filteredStocks.map((stock, index) => (
            <div
              key={stock.value}
              className={`stock-search-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => handleStockSelect(stock)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div className="stock-symbol">{stock.label}</div>
              <div className="stock-name">{stock.name}</div>
            </div>
          ))}
        </div>
      )}
      
      {showDropdown && searchTerm.length > 0 && filteredStocks.length === 0 && (
        <div className="stock-search-dropdown">
          <div className="stock-search-no-results">
            No stocks found matching "{searchTerm}"
          </div>
        </div>
      )}
    </div>
  );
};

export default StockSearchInput;
