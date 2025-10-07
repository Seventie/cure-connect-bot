import React, { useState, useEffect, useRef } from 'react';
import { SearchIcon, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { searchMedicinesRealTime, SearchResponse } from '../services/api';
import { cn } from '../lib/utils';

interface SearchResult {
  drug_name: string;
  medical_condition: string;
  side_effects: string;
  score: number;
}

interface RealTimeSearchProps {
  onResultSelect?: (result: SearchResult) => void;
  placeholder?: string;
  className?: string;
}

const RealTimeSearch: React.FC<RealTimeSearchProps> = ({
  onResultSelect,
  placeholder = "Search medicines, conditions, or symptoms...",
  className
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [totalFound, setTotalFound] = useState(0);
  const [searchTime, setSearchTime] = useState<number | null>(null);
  
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
      setError(null);
      setTotalFound(0);
      setSearchTime(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    const startTime = Date.now();

    console.log(`[RealTimeSearch] Searching for: "${query}"`);

    searchMedicinesRealTime(
      query,
      (response: SearchResponse) => {
        const endTime = Date.now();
        const duration = endTime - startTime;
        setSearchTime(duration);

        console.log(`[RealTimeSearch] Search completed in ${duration}ms`, {
          query,
          totalFound: response.total_found,
          resultsCount: response.results?.length || 0
        });

        if (response.status === 'error') {
          setError(response.query || 'Search failed');
          setResults([]);
          setTotalFound(0);
        } else {
          setResults(response.results || []);
          setTotalFound(response.total_found || 0);
          setIsOpen(true);
          setError(null);
        }
        setIsLoading(false);
        setSelectedIndex(-1);
      },
      300 // 300ms debounce
    );
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < results.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : results.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleResultSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  const handleResultSelect = (result: SearchResult) => {
    console.log('[RealTimeSearch] Result selected:', result);
    setQuery(result.drug_name);
    setIsOpen(false);
    setSelectedIndex(-1);
    onResultSelect?.(result);
  };

  const handleInputFocus = () => {
    if (results.length > 0) {
      setIsOpen(true);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const highlightMatch = (text: string, searchTerm: string) => {
    if (!searchTerm.trim()) return text;
    
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return (
      <span>
        {parts.map((part, index) => 
          regex.test(part) ? (
            <mark key={index} className="bg-yellow-200 font-semibold">
              {part}
            </mark>
          ) : (
            part
          )
        )}
      </span>
    );
  };

  return (
    <div ref={searchRef} className={cn("relative w-full max-w-2xl", className)}>
      {/* Search Input */}
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={handleInputFocus}
          placeholder={placeholder}
          className="pl-10 pr-12 h-11 text-base"
          autoComplete="off"
        />
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
          {isLoading && (
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          )}
          {error && (
            <AlertCircle className="h-4 w-4 text-red-500" title={error} />
          )}
          {!isLoading && !error && results.length > 0 && (
            <CheckCircle className="h-4 w-4 text-green-500" />
          )}
        </div>
      </div>

      {/* Search Stats */}
      {(isLoading || totalFound > 0 || error) && (
        <div className="mt-2 text-sm text-gray-600 flex items-center gap-4">
          {isLoading && (
            <span className="flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Searching...
            </span>
          )}
          {!isLoading && totalFound > 0 && (
            <span>
              Found {totalFound} result{totalFound !== 1 ? 's' : ''}
              {searchTime && ` in ${searchTime}ms`}
            </span>
          )}
          {error && (
            <span className="text-red-600 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {error}
            </span>
          )}
        </div>
      )}

      {/* Search Results Dropdown */}
      {isOpen && (results.length > 0 || error) && (
        <Card className="absolute top-full left-0 right-0 z-50 mt-2 max-h-96 overflow-hidden shadow-lg border">
          <CardContent className="p-0">
            <div 
              ref={resultsRef}
              className="max-h-96 overflow-y-auto"
            >
              {error ? (
                <div className="p-4 text-center text-red-600 flex items-center justify-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </div>
              ) : (
                results.map((result, index) => (
                  <div
                    key={index}
                    className={cn(
                      "p-4 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors",
                      selectedIndex === index 
                        ? "bg-blue-50 border-blue-200" 
                        : "hover:bg-gray-50"
                    )}
                    onClick={() => handleResultSelect(result)}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">
                          {highlightMatch(result.drug_name, query)}
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">
                          <span className="font-medium">Condition:</span>{' '}
                          {highlightMatch(result.medical_condition, query)}
                        </p>
                        {result.side_effects && (
                          <p className="text-xs text-gray-500 mt-2 line-clamp-2">
                            <span className="font-medium">Side effects:</span>{' '}
                            {result.side_effects.length > 100 
                              ? `${result.side_effects.substring(0, 100)}...` 
                              : result.side_effects
                            }
                          </p>
                        )}
                      </div>
                      <div className="flex-shrink-0">
                        <Badge 
                          variant="secondary" 
                          className={cn("text-xs", getScoreColor(result.score))}
                        >
                          {Math.round(result.score * 100)}%
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {/* Footer */}
            {results.length > 0 && (
              <div className="p-3 bg-gray-50 border-t text-xs text-gray-500 text-center">
                Use ↑↓ to navigate, Enter to select, Esc to close
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RealTimeSearch;